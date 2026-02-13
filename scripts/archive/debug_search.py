"""
Debug Search Tool Locally
"""
import os
import sys

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

# Force v4 for this test
os.environ["POLICY_STORE_ID"] = "hr-policy-store-v4"
os.environ["BENEFITS_STORE_ID"] = "hr-policy-store-v4"
os.environ["COMPLIANCE_STORE_ID"] = "hr-policy-store-v4"
os.environ["PAYROLL_STORE_ID"] = "hr-policy-store-v4"
os.environ["ONBOARDING_STORE_ID"] = "hr-policy-store-v4"

from hr_agent.tools.policy_search_tool import search_policy

def main():
    query = "vacation policy"
    print(f"🔎 Searching for: '{query}' in {os.environ['POLICY_STORE_ID']}")
    
    try:
        result = search_policy(query)
        print("\n--- Result ---")
        print(result)
        print("--------------\n")
        
        if "Error" in result or "No relevant" in result:
             print("❌ Search returned an error or no results.")
        else:
             print("✅ Search successful.")
             
    except Exception as e:
        print(f"❌ Exception during search: {e}")

if __name__ == "__main__":
    main()
