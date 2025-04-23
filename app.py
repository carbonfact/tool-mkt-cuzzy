import streamlit as st
import pandas as pd
from rapidfuzz import fuzz

st.set_page_config(page_title="HubSpot Company Matcher", layout="wide")
st.title("🔗 HubSpot Company Matcher with Confidence & Reasoning")

input_file = st.file_uploader("📥 Upload Event Company List (CSV)", type="csv")
hubspot_file = st.file_uploader("📤 Upload HubSpot Export (CSV)", type="csv")

def normalize_domain(domain):
    if pd.isna(domain):
        return ""
    domain = domain.lower().replace("www.", "").replace("corporate.", "")
    domain = domain.split('/')[0]
    return domain.replace(".de", "").replace(".co.uk", "").strip()

if input_file and hubspot_file:
    input_df = pd.read_csv(input_file).fillna('')
    hs_df = pd.read_csv(hubspot_file).fillna('')
    results = []

    for _, row in input_df.iterrows():
        input_name = row['Company Name']
        input_domain = normalize_domain(row.get('Domain', ''))

        best_score = 0
        match_info = {
            "Matched Name": "",
            "Matched Domain": "",
            "HubSpot ID": "",
            "Domain Score": 0,
            "Name Score": 0,
            "Type": "No Good Match",
            "Reason": ""
        }

        # Try exact domain match
        for _, hs_row in hs_df.iterrows():
            hs_domain = normalize_domain(hs_row['HubSpot Domain'])
            if input_domain and input_domain == hs_domain:
                match_info.update({
                    "Matched Name": hs_row['HubSpot Name'],
                    "Matched Domain": hs_domain,
                    "HubSpot ID": hs_row['HubSpot ID'],
                    "Domain Score": 100,
                    "Name Score": fuzz.token_sort_ratio(input_name, hs_row['HubSpot Name']),
                    "Type": "Exact Domain Match",
                    "Reason": "Exact domain match"
                })
                break

        # Fuzzy match if no exact match
        if match_info['Type'] != "Exact Domain Match":
            for _, hs_row in hs_df.iterrows():
                hs_name = hs_row['HubSpot Name']
                hs_domain = normalize_domain(hs_row['HubSpot Domain'])

                domain_score = fuzz.ratio(input_domain, hs_domain) if input_domain else 0
                name_score = fuzz.token_sort_ratio(input_name, hs_name)
                combined_score = max(domain_score, name_score)

                if combined_score > best_score:
                    best_score = combined_score
                    match_info.update({
                        "Matched Name": hs_name,
                        "Matched Domain": hs_domain,
                        "HubSpot ID": hs_row['HubSpot ID'],
                        "Domain Score": domain_score,
                        "Name Score": name_score,
                        "Type": "Fuzzy Domain Match" if domain_score >= name_score else "Fuzzy Name Match",
                        "Reason": f"{'Domain' if domain_score >= name_score else 'Name'} score was higher ({max(domain_score, name_score)}%)"
                    })

        # Filter out poor matches
        if best_score < 60:
            match_info.update({
                "Matched Name": "",
                "Matched Domain": "",
                "HubSpot ID": "",
                "Domain Score": 0,
                "Name Score": 0,
                "Type": "No Good Match",
                "Reason": "No match scored above 60%"
            })

        results.append({
            "Input Company": input_name,
            "Input Domain": input_domain,
            "Matched HubSpot Name": match_info["Matched Name"],
            "Matched Domain": match_info["Matched Domain"],
            "HubSpot ID": match_info["HubSpot ID"],
            "Domain Match Score": f"{match_info['Domain Score']}%",
            "Name Match Score": f"{match_info['Name Score']}%",
            "Final Match Type": match_info["Type"],
            "Match Reason": match_info["Reason"]
        })

    result_df = pd.DataFrame(results)
    st.success("✅ Matching complete!")
    st.dataframe(result_df, use_container_width=True)

    st.download_button("⬇️ Download Results as CSV", result_df.to_csv(index=False), "matched_results.csv", "text/csv")