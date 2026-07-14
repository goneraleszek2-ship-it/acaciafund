import os

from mem0 import Memory


def setup():
    api_key = os.getenv('NVIDIA_API_KEY')
    # Używamy słownika zgodnie z dokumentacją dla wersji, które nie mają mem0.config
    config = {
        "llm": {
            "provider": "nvidia",
            "config": {
                "model": "meta/llama-3.1-405b-instruct",
                "api_key": api_key
            }
        },
        "embedder": {
            "provider": "nvidia",
            "config": {
                "model": "nvidia/embeddings-nv-embed-qa-4",
                "api_key": api_key
            }
        }
    }

    # Przekazujemy config bezpośrednio do konstruktora
    m = Memory(config=config)
    m.add("AcaciaFund to Knowledge Fund skupiony na strukturyzacji wiedzy dziedzinowej.", user_id='leszek_dev')
    print('✅ Sukces! Pamięć została zainicjowana.')

if __name__ == '__main__':
    setup()
