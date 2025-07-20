# File: generative_mapper.py

from gen_utils import query_gen_model

def build_reasoning_prompt(esic_title: str, matches: list, embedding_model: str, gen_model: str, similarity_mode: str, top_k: int = 3):
    prompt = [f"ESIC Title of Category: {esic_title}", ""]
    prompt.append(f"Top {top_k} ISIC semantic matches retrieved via embedding model '{embedding_model}' and similarity metric '{similarity_mode}':")
    prompt.append("")

    for m in matches:
        prompt.append(f"ISIC Code: {m.get('full_code', m.get('code', '')).strip()}")
        # prompt.append(f"  🔹 Level: {m.get('level')}, Sort Order: {m.get('sort_order')}")
        prompt.append(f"  🔹 Description: {m.get('description')}")
        prompt.append(f"  🔹 Section: {m.get('section')} — {m.get('section_label')}")
        prompt.append(f"  🔹 Division: {m.get('division')} — {m.get('division_label')}")
        prompt.append(f"  🔹 Group: {m.get('group')} — {m.get('group_label')}")
        if m.get("explanatory_note_inclusion"):
            prompt.append(f"  ✅ Includes: {m['explanatory_note_inclusion']}")
        if m.get("explanatory_note_exclusion"):
            prompt.append(f"  ❌ Excludes: {m['explanatory_note_exclusion']}")
        prompt.append(f"  📊 Similarity Score: {m.get('score'):.3f}")
        prompt.append("")

    prompt.append(
        "Based on the semantic context, classification structure, and similarity scores provided above, "
        "recommend the most appropriate ISIC classification for the ESIC (Ethiopian Standard Industrial Classification) category. Briefly justify your choice with clear reasoning in no more than 150 words."
    )

    return "\n".join(prompt)

def recommend_best_match(esic_title: str, matches: list, embedding_model: str, gen_model: str, similarity_mode: str, top_k: int = 3):
    prompt = build_reasoning_prompt(esic_title, matches, embedding_model, gen_model, similarity_mode, top_k)
    return query_gen_model(prompt, model_name=gen_model)

