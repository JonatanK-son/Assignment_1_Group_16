import time
import multiprocessing
import re


FILENAME = 'pg2701.txt'

def count_words(chunk):
    """Clean data and count words"""
    # Remove punctuation
    clean_text = re.sub(r'[^\w\s]', '', chunk).lower()
    return len(clean_text.split())

def main():
    
    with open(FILENAME, 'r', encoding='utf-8') as f:
        text = f.read()

    # Split into chunks (Group of lines)
    lines = text.splitlines()
    n_cores = multiprocessing.cpu_count()
    chunk_size = len(lines) // n_cores
    chunks = ["\n".join(lines[i:i + chunk_size]) for i in range(0, len(lines), chunk_size)]

    print(f"Processing {len(lines)} lines using {n_cores} cores.\n")

    # 1. Single Thread
    start = time.time()
    res_single = [count_words(c) for c in chunks]
    total_single = sum(res_single)
    time_single = time.time() - start
    print(f"Single-Thread: {total_single} words in {time_single:.4f} sec")

    # 2. Multi Thread (Multiprocessing)
    start = time.time()
    with multiprocessing.Pool(n_cores) as pool:
        res_multi = pool.map(count_words, chunks)
    total_multi = sum(res_multi)
    time_multi = time.time() - start
    print(f"Multi-Thread:  {total_multi} words in {time_multi:.4f} sec")

    print(f"\nSpeedup Factor: {time_single / time_multi:.2f}x")
    print("Reflection: Multiprocessing overhead might reduce speedup for small tasks, but shines with massive datasets.")

if __name__ == '__main__':
    main()