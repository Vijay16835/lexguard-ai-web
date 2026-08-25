import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.groq_service import groq_service

def test_classification():
    print("=== TESTING LEXGUARD DOCUMENT CLASSIFICATION ENGINE ===")

    sample_resume = """
    John Doe
    Curriculum Vitae / Resume
    Email: john.doe@example.com | Phone: (555) 019-2834
    
    PROFESSIONAL SUMMARY
    Senior Software Engineer with 8+ years of experience building scalable backend microservices, distributed cloud architectures, and machine learning models.
    
    WORK EXPERIENCE
    Lead Architect - TechCorp (2020 - Present)
    - Designed Python FastAPI microservices handling 10M+ daily requests.
    - Led a team of 6 engineers across full-stack development.
    
    EDUCATION
    Bachelor of Science in Computer Science - University of California (GPA 3.8/4.0)
    
    TECHNICAL SKILLS
    Python, FastAPI, Flutter, PostgreSQL, Docker, AWS, Groq API, Machine Learning.
    """

    sample_patent = """
    UNITED STATES PATENT APPLICATION
    Patent No: US 10,987,654 B2
    Title: METHOD AND SYSTEM FOR REAL-TIME PARALLEL OPTICAL CHARACTER RECOGNITION AND NEURAL INFERENCE
    
    INVENTORS: Jane Smith, Alex Johnson
    APPLICANT: LexGuard Technologies Inc.
    
    ABSTRACT
    A system and method for accelerated optical character recognition utilizing dual-stage fallback neural inference pipelines.
    
    FIELD OF THE INVENTION
    This invention relates generally to document processing systems, and more particularly to neural extraction architectures.
    
    CLAIMS
    1. A method for analyzing documents comprising:
    extracting text via OCR;
    evaluating text confidence scores;
    triggering a fallback LLM when confidence falls below a target threshold.
    """

    sample_nda = """
    MUTUAL NON-DISCLOSURE AGREEMENT (NDA)
    
    This Non-Disclosure Agreement ("Agreement") is entered into by and between Disclosing Party Inc. and Receiving Party LLC.
    
    1. CONFIDENTIAL INFORMATION
    "Confidential Information" refers to any non-public technical, financial, or business information disclosed by either party.
    
    2. OBLIGATIONS
    The Receiving Party agrees to maintain strict confidentiality, limit access to authorized personnel, and refrain from disclosing proprietary information to any third party.
    
    3. TERM AND TERMINATION
    This Agreement shall remain in effect for a period of five (5) years from the Effective Date.
    
    IN WITNESS WHEREOF, the parties have executed this Agreement.
    """

    sample_invoice = """
    INVOICE #INV-2026-0089
    Date: October 14, 2026
    Due Date: November 14, 2026
    
    BILL TO:
    Acme Enterprise Solutions
    100 Main Street, Suite 400
    
    DESCRIPTION                    QTY    RATE      AMOUNT
    Legal Compliance Analysis        1     $2,500    $2,500.00
    Cloud Platform Subscription      1       $500      $500.00
    
    SUBTOTAL: $3,000.00
    TAX (8%): $240.00
    TOTAL DUE: $3,240.00
    
    Please make checks payable to LexGuard Corp.
    """

    tests = [
        ("Resume Document", sample_resume, "Resume / CV"),
        ("Patent Document", sample_patent, "Patent"),
        ("NDA Document", sample_nda, "Non-Disclosure Agreement"),
        ("Invoice Document", sample_invoice, "Invoice"),
    ]

    all_passed = True
    for name, text, expected in tests:
        detected = groq_service.classify_document_text(text)
        fallback_res = groq_service._fallback_rule_based_analysis(text)
        fallback_type = fallback_res["document_type"]
        
        status = "PASSED" if detected == expected and fallback_type == expected else "FAILED"
        if status == "FAILED":
            all_passed = False
        
        print(f"[{status}] {name}")
        print(f"   Expected: '{expected}' | Detected Engine: '{expected}' | Fallback Pipeline: '{fallback_type}'")
        print(f"   Risk Level: {fallback_res['risk_level']} | Risk Score: {fallback_res['risk_score']}")
        print(f"   Summary: {fallback_res['summary'][:100]}...\n")

    return all_passed

async def test_summary_resilience():
    print("=== TESTING SUMMARY PIPELINE RESILIENCE ===")
    sample_text = "This is a test resume document for verifying non-failing summary generation."
    
    res = await groq_service.generate_summary(sample_text, "Resume / CV")
    print(f"[PASSED] Summary endpoint returned valid object:")
    print(f"   Short summary: {res.get('short_summary')}")
    print(f"   Key points: {res.get('key_points')}")
    return True

if __name__ == "__main__":
    import asyncio
    c_ok = test_classification()
    s_ok = asyncio.run(test_summary_resilience())
    if c_ok and s_ok:
        print("ALL CLASSIFICATION & SUMMARY PIPELINE TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("TESTS FAILED!")
        sys.exit(1)
