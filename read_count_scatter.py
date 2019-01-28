#!/usr/bin/env python3
"""read_count_scatter.py

"""

import sys
import argparse
import warnings
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import chi2_contingency
from statsmodels.stats.multitest import multipletests
from matplotlib.pyplot import savefig

def write_dict(tsv_file):
    """takes a tsv file and reads it as a dictionary
    tsv_file : input tsv file
    read_count_dict : ouput dictionary
    dictionary keys : gene names
    dictionary values : read count (int)"""
    read_count_dict = {} #initialise dictionary
    with open(tsv_file) as f:
        next(f) #skipping the header
        for line in f:
            (k, v) = line.split('\t')
            try:
                read_count_dict[k.strip()] = int(float(v.strip())) #to catch high readcounts entered as eg. 1e8
            except ValueError:
                print('Gene {} has invalid readcount value: "{}".'.format(k.strip(), v.strip()))
                exit #sys.exit(1)
    return(read_count_dict)

def missing_genes(dict_a, dict_b):
    """find gene names that are in (sample A but not B) and (sample B but not A)
    dict_a : dictionary (k=gene names, v=read count(int))
    dict_b : dictionary (k=gene names, v=read count(int))
    returns a warning if a gene name is found in one sample dictionary but not the other"""
    buddyless_genes_a = []
    buddyless_genes_b = []
    for gene in dict_a.keys():
        if gene not in dict_b.keys():
            buddyless_genes_a.append(gene)
            if len(buddyless_genes_a) > 0:
                warnings.warn("Warning: Gene {} was not found in Sample B.".format(gene.strip()))
    for gene in dict_b.keys(): 
        if gene not in dict_a.keys():
            buddyless_genes_b.append(gene)
            if len(buddyless_genes_b) > 0:
                warnings.warn("Warning: Gene {} was not found in Sample A.".format(gene.strip()))
    return(True)

def read_count_sig(dict_a, dict_b):
    """dict_a , dict_b : dictionary
    takes two dictionaries, calculates the total readcounts for each dictionary(sample). 
    if the same gene is in both samples, it determines the readcount for the gene in each sample.
    if the readcount does not equal 0 in both cases, a chi squared test is performed.
    the test values for chi squared are the gene readcount for each sample and the total readcounts of each sample.
    output : tuple of numpy arrays of sample a readcounts, sample b readcounts, all pvalues"""
    total_read_count_a = sum(dict_a.values())
    total_read_count_b = sum(dict_b.values())
    all_a_readcounts = []
    all_b_readcounts = []
    all_pvalues = []
    missing_genes(dict_a, dict_b)
    for gene in dict_a.keys():
        if gene in dict_b.keys():
            count_a = dict_a[gene]
            count_b = dict_b[gene]
        if (count_a == 0) and (count_b == 0): #chisquared won't work with both 0s
            all_a_readcounts.append(count_a)
            all_b_readcounts.append(count_b)
            all_pvalues.append(1.0) #the difference between readcount=0 and readcount=0 will never be significant
        else:
            contingency_table = np.array([[count_a, (total_read_count_a - count_a)], [count_b, (total_read_count_b - count_b)]])
            chi2_output = chi2_contingency(contingency_table)
            all_a_readcounts.append(count_a)
            all_b_readcounts.append(count_b)
            all_pvalues.append(chi2_output[1])
    return(np.array(all_a_readcounts), np.array(all_b_readcounts), np.array(all_pvalues)) #returns tuple of numpy arrays

def read_count_scatter(x, y, sig_or_not, scatter_name):
    """writes a scatterplot of gene counts for each sample, colour-coded for significance, to a pdf
    x : sample a readcounts (np.array)
    y : sample b readcounts (np.array)
    sig_or_not : pvalues corrected for multiple testing (np.array, boolean), True=hypothesis rejected for alpha=0.05"""
    plt.scatter(x[sig_or_not],y[sig_or_not], label='Significant', c='r') #significant read count differences coloured red
    plt.scatter(x[~sig_or_not], y[~sig_or_not], label='Not Significant', c='b') #nonsig read count differences coloured blue
    plt.title("Gene Read Counts")
    plt.xlabel("Sample A Read Counts")
    plt.ylabel("Sample B Read Counts")
    plt.legend()
    savefig(scatter_name+'.pdf')

if __name__ == '__main__': #only need this for command line executable. Not relevant for ipython notebook usage. only thing that gets called whehn you use the script
	#use argparse to handle command line arguments
	parser = argparse.ArgumentParser()
	parser.add_argument("sample_a", help="first input file (tsv) with readcounts")
	parser.add_argument("sample_b", help="second input file (tsv) with readcounts")
	parser.add_argument("scatter_name", help="base name for scatter .pdf file")
	args = parser.parse_args()

	sample_a_dict = write_dict(args.sample_a)
	sample_b_dict = write_dict(args.sample_b)
	x, y, pvals = read_count_sig(sample_a_dict, sample_b_dict)
	p_adjusted = multipletests(pvals, alpha=0.05, method='fdr_bh', is_sorted=False, returnsorted=False) #calc padj
	sig_or_not = p_adjusted[0]
	read_count_scatter(x, y, sig_or_not, args.scatter_name)
	print('Created file called {}.pdf'.format(args.scatter_name) )

sys.exit(0)