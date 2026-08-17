import os
import yaml
import numpy as np
import math
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from uuid import UUID

logger = logging.getLogger(__name__)

class MemoryScapeRetriever:
    def __init__(self, scape_path: str, vector_db):
        self.scape_path = scape_path
        self.vdb = vector_db
        
    def _parse_markdown(self, filepath: str) -> Dict:
        """Parses frontmatter and body from a memory node."""
        if not os.path.exists(filepath):
            return {}
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Split frontmatter
            if content.startswith('---'):
                try:
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        fm, body = parts[1], parts[2]
                        metadata = yaml.safe_load(fm)
                        return {"metadata": metadata, "body": body.strip()}
                except yaml.YAMLError as e:
                    logger.error(f"YAML parsing error in {filepath}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error parsing {filepath}: {e}")
        return {}

    def calculate_temperature(self, metadata: Dict) -> float:
        """Calculate Ebbinghaus forgetting curve temperature."""
        base_importance = metadata.get('confidence', 0.5)
        last_accessed_val = metadata.get('last_accessed')
        
        if not last_accessed_val:
            return base_importance
            
        try:
            # Check if pyyaml already parsed it as datetime
            if isinstance(last_accessed_val, datetime):
                last_accessed = last_accessed_val
            else:
                last_accessed = datetime.fromisoformat(str(last_accessed_val))
                
            now = datetime.now(timezone.utc)
            
            # Ensure timezone awareness
            if last_accessed.tzinfo is None:
                last_accessed = last_accessed.replace(tzinfo=timezone.utc)
                
            time_since = (now - last_accessed).total_seconds()
            
            # e^(-Decay_Rate * Time_Since_Last_Access)
            # Assuming a decay rate corresponding to a 30-day half-life: ln(2) / (30 * 24 * 3600)
            decay_rate = 2.67e-7 
            
            temperature = base_importance * math.exp(-decay_rate * time_since)
            return temperature
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing date {last_accessed_val}: {e}")
            return base_importance
        except Exception as e:
            logger.error(f"Unexpected error calculating temperature: {e}")
            return base_importance

    def _lexical_search(self, query: str, top_k: int) -> List[Any]:
        """Mock implementation of BM25 / Lexical Search."""
        logger.info(f"Performing lexical search for query: {query}")
        # In a real scenario, this would use a BM25 index over the documents
        # Returning empty list as a mock for now
        return []

    def retrieve(self, query: str, top_k: int = 5, hop_depth: int = 1) -> List[Dict]:
        """Hybrid search (Semantic + Lexical) with graph traversal using RRF."""
        # Step 1: Semantic Search
        query_vector = self.vdb.embed(query)
        semantic_hits = self.vdb.search(query_vector, top_k=top_k)
        
        # Step 1.5: Lexical Search (BM25 Mock)
        lexical_hits = self._lexical_search(query, top_k=top_k)
        
        # Reciprocal Rank Fusion (RRF)
        rrf_scores = {}
        k_rrf = 60
        
        for rank, hit in enumerate(semantic_hits):
            if hasattr(hit, 'id'):
                rrf_scores[hit.id] = rrf_scores.get(hit.id, 0) + 1.0 / (k_rrf + rank + 1)
            
        for rank, hit in enumerate(lexical_hits):
            if hasattr(hit, 'id'):
                rrf_scores[hit.id] = rrf_scores.get(hit.id, 0) + 1.0 / (k_rrf + rank + 1)
            
        # Sort by RRF score and get top_k IDs
        sorted_hits = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:top_k]
        
        context_nodes = []
        visited = set()
        
        # Step 2: Graph Expansion
        for hit_id in sorted_hits:
            if hit_id in visited:
                continue
                
            node_data = self._parse_markdown(os.path.join(self.scape_path, f"{hit_id}.md"))
            
            # Skip invalid or archived nodes
            if not node_data or node_data.get('metadata', {}).get('archived', False):
                continue
                
            context_nodes.append(node_data)
            visited.add(hit_id)
            
            # Expand relations up to hop_depth
            if hop_depth > 0:
                relations = node_data['metadata'].get('related', []) + node_data['metadata'].get('children', [])
                for rel_id in relations[:3]: # Cap expansion
                    if rel_id not in visited:
                        rel_data = self._parse_markdown(os.path.join(self.scape_path, f"{rel_id}.md"))
                        if rel_data and not rel_data.get('metadata', {}).get('archived', False):
                            context_nodes.append(rel_data)
                            visited.add(rel_id)
                        
        return self._rank_and_format(context_nodes, query)
        
    def _rank_and_format(self, nodes: List[Dict], query: str) -> List[Dict]:
        """Rank nodes based on Ebbinghaus forgetting curve temperature."""
        return sorted(nodes, key=lambda x: self.calculate_temperature(x.get('metadata', {})), reverse=True)
