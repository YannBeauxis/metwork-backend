import itertools

import numpy as np

def generate_network(scores_matrix, mzs, top_k, pairs_min_cosine, use_self_loops=False): #TODO: change this in worker
    interactions = []
    num_spectra = len(mzs)

    triu = np.triu(scores_matrix)
    triu[triu <= pairs_min_cosine] = 0
    for i in range(num_spectra):
        # indexes = np.argpartition(triu[i,], -options.top_k)[-options.top_k:] # Should be faster and give the same results
        indexes = np.argsort(triu[i,])[-top_k:]
        indexes = indexes[triu[i, indexes] > 0]

        for index in indexes:
            interactions.append((i, index, mzs[i]-mzs[index], triu[i, index]))

    interactions = np.array(interactions, dtype=[('Source', int), ('Target', int), ('Delta MZ', np.float32), ('Cosine', np.float32)])
    interactions = interactions[np.argsort(interactions, order='Cosine')[::-1]]

    # Top K algorithm, keep only edges between two nodes if and only if each of the node appeared in each other’s respective top k most similar nodes
    mask = np.zeros(interactions.shape[0], dtype=bool)
    for i, (x, y, _, _) in enumerate(interactions):
        x_ind = np.where(np.logical_or(interactions['Source']==x, interactions['Target']==x))[0][:top_k]
        y_ind = np.where(np.logical_or(interactions['Source']==y, interactions['Target']==y))[0][:top_k]
        if (x in interactions[y_ind]['Source'] or x in interactions[y_ind]['Target']) \
          and (y in interactions[x_ind]['Source'] or y in interactions[x_ind]['Target']):
            mask[i] = True
    interactions = interactions[mask]

    # Add selfloops for individual nodes without neighbors
    if use_self_loops:
        unique = set(itertools.chain.from_iterable((x['Source'], x['Target']) for x in interactions))
        selfloops = set(range(0, triu.shape[0])) - unique
        size = interactions.shape[0]
        interactions.resize((size + len(selfloops)))
        interactions[size:] = [(i, i, 0., 1.) for i in selfloops]

    return interactions
