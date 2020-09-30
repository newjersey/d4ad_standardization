"""
This is a giant list of canonical sources of non-governmental approval.

The key is the canonical name for that non-government approval, the values
includes variations of that name. Both the variations nad canonical name
are searched via regex, to construct a list of canonical names. 

Casing does not matter (they are searched with everything lower cased)
"""

nongov =\
{
    "National Healthcare Association":\
        {
            'NHA',
        },
    "Accrediting Commission of Career Schools and Colleges":\
        {
            "ACCSC",
            'A.C.C.S.C.'
        },
    "Accrediting Commission of Career Schools and Colleges of Technology":\
        {
            "ACCSCT"
        },
    "Veteran":\
        {
            "Veteran"
        },
    "Commission on Accreditation of Rehabilitation Facilities":\
        {
            "CARF",
            "The Rehabilitation Accreditation Commission"
        },
    "Middle States Association of Colleges and Schools":\
        {
            "MSA-CESS",
            "MSA",
            "MSASC",
            "M.S.A",
            "M.S.A.S.C",
            "Middle States Association",
            "Association of Middle States",
            "Mid-Atlantic States"
        },
    "International Association for Continuing Education and Trainings":\
        {
            "IACET"
        },
    "Accrediting Council for Independent Colleges and Schools":\
        {
            'A.C.I.C.S.'
        },
    "Accrediting Council for Continuing Education & Training":\
        {
            "ACCET"
        },
    "Association of Internet Professionals":\
        {
            "SIP"
        },
    "Corporation":\
        {
            "Microsoft",
            "IBM",
            "Cisco",
            "AT&T",
            "Prometric",
            "Vue",
            "Siebel",
            "Novell",
            "Cisco",
            "Hewlett Packard",
            "Compaq",
            "IBM",
            "3Com",
            "SCO",
            "Lucent",
            "Lotus",
            "Oracle"
        },
    "Council on Occupational Education":\
        {
            "COE"
        },
    "American Massage Therapy Association Counsel of Schools":\
        {
            "AMTA"
        },
    "CompTIA":\
        {
        "Computing Technology Industry Association"
        },
    "DOE-Professional Development Provider":\
        {
            "DOE",
            "Department of Education",
            "NJDOE"
        },
    "The Joint Commission on Accreditation of Healthcare Organizations":\
        {
            "JCAHO"
        },
    "Professional Truck Driving Institute":\
        {
        },
    "NY/NJ MINORITY PURCHASING COUNCIL":\
        {
        },
    "Joint Review Committee on Education in Radiologic Technology":\
        {
         "JRCERT"
        },
    "RAPIDS":\
        {
            "rapid"
        },
    "National Accrediting Commission of Cosmetology Arts and Sciences":\
        {
         "NACCAS"
        },
    "WIB":\
        {
        },
    "University":\
        {
        },
    "US Dept of Labor":\
        {
         "OSHA",
         "DOL"
        },
    "National Center for Construction Education and Research":\
        {
         "NCCER"
        },
    "ProLiteracy":\
        {
        },
    "Title":\
        {
            "WIOA",
            "WIA"
        },
    "Work First":\
        {
         "WFNJ"
        },
    "Commission on Accreditation of Allied Health Education Programs":\
        {
         ""
        },
    "Addiction Professionals Certification Board of NJ":\
        {
         "Addiction Professionals Certification"
        },
    "Non-profit":\
        {
         "non-profit",
         "nonprofit"
        },
    "Faith Based":\
        {
         "faith",
         "faith-based"
        },
    "National Association of Myofascial Trigger Point Therapists":\
        {
         "NAMTPT"
        },
    "Associated Bodywork & Massage Professionals":\
        {
         "ABMP"
        },
    "National Certification Board for Therapeutic Massage & Bodywork":\
        {
         "ncbtmb"
        },
    "National Environmental Health Association":\
        {
         "NEHA"
        },
    "National Radon Safety Board":\
        {
         "NRSB"
        },
    "The Electronics Technicians Association International":\
        {
         "ETA International",
         "ETAI"
        },
    "Middle States Commission and Council on Occupational Education":\
        {
         "MSCCOE",
         "Middle States Commission"
        },
    "The American Medical Certification Association":\
        {
         "AMCA"
        },
    "American Association of Medical Assistants":\
        {
         "AAMA"
        },
    "Depart of Health":\
        {
         "Dept. of Health",
         "DOH"
        },
    "American Society of Phlebotomy Technicians":\
        {
         "ASPT"
        },
    "GAINS":\
        {
         "gain",
         "gains"
        },
    "Security Officer Training Association":\
        {
         "SORA"
        },
    "Addiction Professional Certification Board":\
        {
         "APDC"
        },
    "Real Estate Commission":\
        {
         "Real Estate Commission"
        },
    "US Environmental Protection Agency":\
        {
         "EPA"
        },
    "Child and Adolescent Health Centers":\
        {
         "CAHC"
        },
    "Commission on Accreditation of Allied Health Education Programs":\
        {
         "CAAHEP"
        },
    "Accrediting Bureau of Health Education Schools":\
        {
         "ABHES"
        },
    "NYS BPSS":\
        {
         "BPSS"
        },
    "Association for Supply Chain Management":\
        {
         "APICS",
        },
    "Office of Higher Education":\
        {
         "Higher Ed",
         "OHE",
         "NYSED"
        },
    "American Registry of Magnetic Resonance Imaging Technologists":\
        {
         "ARMRIT"
        },
    "National Center for Competency Testing":\
        {
         "NCCT"
        },
    "Accreditation Board for Engineering and Technology":\
        {
         "ABET"
        },
    "TAC//ABET":\
        {
         "Technology Accreditation Commission/Accreditation Board for Engineering and Technology"
        },
    "Department of Health & Senior Services":\
        {
         "DHSS"
        },
    "Commission on Massage Therapy Accreditation":\
        {
         "COMTA"
        },
    "Accrediting Commission of Career Schools and Colleges":\
        {
         "Accrediting Commission of Career"
        },
    "Accreditation Council for Continuing Medical Education":\
        {
         "ACCME"
        },
    "Division of Developmental Disabilities":\
        {
         "Division of Developmental Disabilities"
        },
    "North American Board of Certified Energy Practitioners":\
        {
         "NABCEP"
        },
    "American Institute of Architects":\
        {
         "AIA"
        },
    "Distance Education and Training Council":\
        {
         "DEAC",
         "D.E.T.C."
        },
    "NJ Board of Nursing":\
        {
         "NJ Board of Nursing",
         "Board of nursing"
        },
    "American Council on Education":\
        {
         "ACE"
        },
    "Division of Vocational Rehabilitation Services":\
        {
         "DVRS"
        },
    "Division of Mental Health and Hygiene":\
        {
         "DMHH"
        },
    "Department of Health and Senior Services":\
        {
         "DOHSS"
        },
    "Substance Abuse and Mental Health Services":\
        {
         "SAMSHA"
        }
}