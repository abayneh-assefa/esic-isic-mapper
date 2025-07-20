Disclaimer:
This application is not production ready implementation with an intention to only to support internal group of experts working on harmonizing Ethiopian industrial classifications with international best practices. Hence, we do not suggest building production environments with this code base as is. 



📘 ESIC–ISIC Semantic Mapper
    This application uses vector similarity to semantically map 
    Ethiopian Standard Industrial Classification (ESIC) entries to 
    the International Standard Industrial Classification (ISIC Rev. 4 or 5). 
    It includes both a command-line pipeline and an interactive web UI.


✅ System Features Overview
    Feature	                                Capability
    Vector Embedding	                   Semantic similarity using mxbai-embed-large, nomic-embed-text or bge-m3, 
    Multi-label Support	                   Assigns multiple ISIC codes per ESIC title (Top-K)
    Export      	                       Results saved to Excel with score rankings
    Web UI	                               Streamlit-powered interface for live queries

🚀 Test Results 
    Below is a result based on mappiong done to help matching of Ethiopin industrial classification used for business licensing with the closest ISIC Rev.5 class.
   
    N.th Match              Count of ESIC Code
        1	                    282
        2	                    52
        3	                    28
        4	                    26
        5	                    17
        6 or more	            135
    -----------------------------------------
 	    Grand Total	            540
    =========================================


🌐 Launch the Web Interface
    Simply run:  docker compose up --build
    Then visit Web UI:  🌐 http://localhost:8501


🧪 Pipeline Commands
    Once the container is running, use: docker compose exec app python pipeline.py <command>

    Command     	Description
    loadesic	    Load ESIC records from Excel and embed titles
    loadisic	    Load ISIC records and embed descriptions
    map	            Match ESIC to ISIC using cosine similarity
    export	        Export matches to mapping_results.xlsx
    loadmap	        Runs load + loadisic + map sequentially
    reset	        Clears MongoDB data (ESIC, ISIC, results)
    test	        Test the embedding service
    --help	        Show command usage info

    Example commands:
        python pipeline.py reset
        python pipeline.py loadisic
        python pipeline.py loadesic
        python pipeline.py map
        python pipeline.py export

    Show CLI help:
        docker compose exec app python pipeline.py --help



⚡ Run Full Mapping Flow 
    docker compose exec app python pipeline.py reset
    docker compose exec app python pipeline.py loadmap

    These commands will:
        🧹 Clear existing collections
        📥 Import ESIC & ISIC records with vector embeddings
        🔍 Perform ESIC→ISIC matching
        💾 Save results to MongoDB



📤 Export to Excel. The output file will be saved int output directory.
    docker compose exec app python pipeline.py export

    

🧪 Test embedding connectivity:
    docker compose exec app python pipeline.py test

