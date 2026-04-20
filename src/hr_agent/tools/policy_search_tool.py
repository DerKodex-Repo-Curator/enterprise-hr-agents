from google.cloud import discoveryengine # type: ignore
from google.api_core.client_options import ClientOptions
import os

from hr_agent.config import PROJECT_ID

LOCATION = "global"

def _search(query: str, data_store_id: str) -> str:
    """Internal helper to search a specific data store."""
    try:
        client = discoveryengine.SearchServiceClient(
            client_options=ClientOptions(
                api_endpoint=f"discoveryengine.googleapis.com"
            )
        )
        
        serving_config = client.serving_config_path(
            project=PROJECT_ID,
            location=LOCATION,
            data_store=data_store_id,
            serving_config="default_config",
        )
        
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=5,
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                    return_snippet=True,
                ),
            ),
            query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
                condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
            ),
            spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
                mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
            ),
        )

        response = client.search(request)
        
        results_text = []
        for result in response.results:
            doc_data = result.document.derived_struct_data
            title = doc_data.get("title", "Untitled Document")
            link = doc_data.get("link", "")
            
            snippets = []
            if "snippets" in doc_data:
                for s in doc_data["snippets"]:
                    if "snippet" in s:
                        snippets.append(s["snippet"])
            
            snippet_text = "\n".join(snippets)
            result_entry = f"Title: {title}\n"
            if link:
                result_entry += f"Link: {link}\n"
            result_entry += f"Content: {snippet_text}\n"
            results_text.append(result_entry)
            
        if not results_text:
            return "No relevant documents found for your query."
            
        return "\n---\n".join(results_text)
        
    except Exception as e:
        # Log identity and error details server-side only — never expose SA email or raw
        # API errors to end users, as they reveal internal GCP project/SA information.
        try:
            import google.auth
            import requests
            metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email"
            headers = {"Metadata-Flavor": "Google"}
            sa_email = requests.get(metadata_url, headers=headers, timeout=5).text
        except Exception:
            sa_email = "unknown_identity"
        print(f"[policy_search] Error: {str(e)} (Running as: {sa_email})")

        return "I was unable to retrieve the relevant documents. Please try again or contact HR directly."


# Store IDs
POLICY_STORE_ID = os.getenv("POLICY_STORE_ID", "hr-policy-store-v4")
COMPLIANCE_STORE_ID = os.getenv("COMPLIANCE_STORE_ID", "hr-policy-store-v4")
BENEFITS_STORE_ID = os.getenv("BENEFITS_STORE_ID", "hr-policy-store-v4")
PAYROLL_STORE_ID = os.getenv("PAYROLL_STORE_ID", "hr-policy-store-v4")
ONBOARDING_STORE_ID = os.getenv("ONBOARDING_STORE_ID", "hr-policy-store-v4")

def search_policy(query: str) -> str:
    """Searches the HR policy documents for relevant information.
    
    Args:
        query: The search query (e.g., 'vacation policy', 'sick leave', 'termination procedure').
    Returns:
        Relevant excerpts from the policy documents.
    """
    lower_query = query.lower()
    results = []
    
    # Base search
    base_query = query
    if "international" in lower_query or "limit" in lower_query:
         base_query += " tax data security manager approval"
    elif "nepotism" in lower_query or "relative" in lower_query:
         base_query += " hiring relatives family members"
         
    primary_result = _search(base_query, POLICY_STORE_ID)
    results.append(primary_result)

    # Heuristic expansions for related stores
    if "surgery" in lower_query or "medical" in lower_query or "leave" in lower_query:
        # Also check benefits for STD/LTD
        results.append(_search("short term disability FMLA", BENEFITS_STORE_ID))
        
    if "conflict" in lower_query or "business" in lower_query:
        # Also check compliance for reporting forms
        results.append(_search("conflict of interest reporting form approval", COMPLIANCE_STORE_ID))

    if "payroll" in lower_query or "paycheck" in lower_query or "salary" in lower_query or "compensation" in lower_query:
         # Also check payroll specific store
         payroll_res = _search("payroll error discrepancy", PAYROLL_STORE_ID)
         results.append(payroll_res)
         
         # If no documents found in any store, return a clear message rather than mock data
         combined_text = "\n".join(results)
         if "Title:" not in combined_text:
             return "No payroll documents found. Please contact the Payroll Department directly or submit a ticket via the HR Portal."

    return "\n---\n".join(results)

def search_compliance(query: str) -> str:
    """Searches compliance and regulatory documents.
    
    Args:
        query: The search query (e.g., 'EEOC guidelines', 'OSHA safety', 'GDPR').
    Returns:
        Relevant excerpts from compliance documents.
    """
    return _search(query, COMPLIANCE_STORE_ID)

def search_benefits(query: str) -> str:
    """Searches employee benefits documents.
    
    Args:
        query: The search query (e.g., 'health insurance', '401k', 'dental plan').
    Returns:
        Relevant excerpts from benefits documents.
    """
    return _search(query, BENEFITS_STORE_ID)

def search_payroll(query: str) -> str:
    """Searches payroll and compensation documents.
    
    Args:
        query: The search query (e.g., 'direct deposit', 'tax withholding', 'bonus structure').
    Returns:
        Relevant excerpts from payroll documents.
    """
    return _search(query, PAYROLL_STORE_ID)

def search_onboarding(query: str) -> str:
    """Searches onboarding and new hire documents.
    
    Args:
        query: The search query (e.g., 'first day checklist', 'IT setup', 'orientation').
    Returns:
        Relevant excerpts from onboarding documents.
    """
    return _search(query, ONBOARDING_STORE_ID)

