import json
import os
import threading

from yaca.llm import LLMClient


def test_llm_cache_concurrency_threaded(tmp_path) -> None:
    cache_file = os.path.join(str(tmp_path), "llm_cache.json")
    client = LLMClient(cache_file=cache_file)

    n_threads = 10
    m_writes_per_thread = 50

    def worker(tid: int) -> None:
        for i in range(m_writes_per_thread):
            key = f"t{tid}-k{i}"
            value = {"thread": tid, "i": i}
            client._set_cache_key(key, value)

    threads = []
    for t in range(n_threads):
        th = threading.Thread(target=worker, args=(t,))
        th.start()
        threads.append(th)

    for th in threads:
        th.join()

    with open(cache_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == n_threads * m_writes_per_thread

    assert data["t0-k0"] == {"thread": 0, "i": 0}
    assert data[f"t{n_threads - 1}-k{m_writes_per_thread - 1}"] == {
        "thread": n_threads - 1,
        "i": m_writes_per_thread - 1,
    }
