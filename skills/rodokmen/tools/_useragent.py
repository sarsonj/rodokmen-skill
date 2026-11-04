"""Jediný User-Agent všech nástrojů (načítá ho tools/slusne.py, nástroje ho berou jako slusne.UA, curl přes slusne.py taky).

„rodokmen“ v něm nech: archivy podle něj nástroj poznají (SOA Třeboň a SOA Praha ho zakázaly) – jiný User-Agent
by byl obcházení zákazu.
"""
UA = "Mozilla/6.0 (rodokmen)"
