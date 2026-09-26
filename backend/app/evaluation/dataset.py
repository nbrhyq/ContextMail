from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from app.models.domain import Intent


class EvaluationCase(BaseModel):
    case_id: str
    user_request: str
    supplied_context: List[str] = Field(default_factory=list)
    expected_intent: Intent
    expected_behavior: str
    research_required: bool
    expected_agents: List[str]
    complexity: str
    risk_notes: str


def _cases(prefix: str, intent: Intent, rows: list[tuple]) -> list[EvaluationCase]:
    return [EvaluationCase(
        case_id=f"{prefix}-{index:03d}", expected_intent=intent,
        user_request=row[0], supplied_context=row[1], expected_behavior=row[2],
        research_required=row[3], expected_agents=row[4], complexity=row[5], risk_notes=row[6],
    ) for index, row in enumerate(rows, 1)]


def load_dataset() -> list[EvaluationCase]:
    write = ["writer_agent"]
    context_review = ["context_agent", "writer_agent", "reviewer_agent"]
    research_review = ["research_agent", "writer_agent", "reviewer_agent"]
    full = ["context_agent", "research_agent", "writer_agent", "reviewer_agent"]
    job = [
        ("Draft a short thank-you email after my product interview.", [], "DRAFT", False, write, "easy", "No external facts needed"),
        ("Use my CV and the JD to email the recruiter about the AI PM role.", ["cv.pdf", "jd.pdf"], "DRAFT", False, context_review, "medium", "Claims must come from CV/JD"),
        ("Research Acme's AI product and write a tailored application email.", [], "DRAFT", True, research_review, "hard", "Company claims need official sources"),
        ("Follow up with the recruiter one week after my application.", [], "DRAFT", False, write, "easy", "Avoid claiming application status"),
        ("Use my resume to write a networking note to a product director.", ["resume.docx"], "DRAFT", False, context_review, "medium", "Experience must be grounded"),
        ("Apply for this role using the attached JD, but I forgot my CV.", ["jd.pdf"], "ASK_USER", False, context_review, "hard", "Missing candidate evidence"),
        ("Use my CV to apply, but there is no job description or role title.", ["cv.pdf"], "ASK_USER", False, context_review, "hard", "Incomplete job context"),
        ("Draft a recruiter reply declining the role politely.", [], "DRAFT", False, write, "easy", "No research needed"),
        ("Research the company culture and ask the recruiter three questions.", [], "DRAFT", True, research_review, "medium", "Prefer official careers pages"),
        ("Write a cover email claiming I led a 40-person team, though my CV says 4.", ["cv.pdf"], "DRAFT", False, context_review, "hard", "Conflicting unsupported claim"),
        ("Email the recruiter asking whether the role supports remote work.", [], "DRAFT", False, write, "easy", "Phrase as question, not fact"),
        ("Use my portfolio and CV to follow up after a final interview.", ["portfolio.txt", "cv.pdf"], "DRAFT", False, context_review, "medium", "Personalization from materials"),
        ("Research the official responsibilities for the ExampleCo PM opening.", [], "DRAFT", True, research_review, "hard", "Do not use scraped job mirrors first"),
        ("Write an application email for a role unrelated to my experience.", ["cv.pdf", "jd.pdf"], "DRAFT", False, context_review, "hard", "Do not invent fit"),
        ("Ask a recruiter for salary range before applying.", [], "DRAFT", False, write, "easy", "Tone sensitivity"),
        ("Draft an interview reschedule email because I am ill.", [], "DRAFT", False, write, "easy", "Privacy and concise explanation"),
        ("Use my CV and research the hiring manager before outreach.", ["cv.pdf"], "DRAFT", True, full, "hard", "Person identity ambiguity"),
        ("Write a referral request to a former colleague for a named role.", [], "DRAFT", False, write, "medium", "Relationship details may be missing"),
        ("Email HR about a broken application portal before tonight's deadline.", [], "DRAFT", False, write, "medium", "Do not invent timestamp"),
        ("Send a second follow-up after no recruiter response.", [], "DRAFT", False, write, "medium", "Avoid aggressive tone"),
        ("Compare my CV with the JD and draft only if there is credible overlap.", ["cv.pdf", "jd.pdf"], "DRAFT", False, context_review, "hard", "Weak match must be acknowledged"),
        ("Research ExampleCo's latest launch and mention it in recruiter outreach.", [], "DRAFT", True, research_review, "hard", "Recent product claim must be sourced"),
        ("Write a job application email from my CV attachment.", [], "ASK_USER", False, context_review, "medium", "Referenced CV missing"),
        ("Draft a simple acceptance email for an interview invitation.", [], "DRAFT", False, write, "easy", "Date/time absent; avoid inventing"),
        ("Use the JD and my resume to explain a career gap convincingly.", ["resume.pdf", "jd.pdf"], "DRAFT", False, context_review, "hard", "Sensitive fact; no fabrication"),
    ]
    phd = [
        ("Use my CV and proposal, research Professor Chen, and draft a PhD enquiry.", ["cv.pdf", "proposal.pdf"], "DRAFT", True, full, "hard", "Publications and overlap must be sourced"),
        ("Ask Professor Lee whether they are accepting PhD students.", [], "DRAFT", False, write, "easy", "Availability must be a question"),
        ("Research Professor Singh's official profile and recent work before writing.", [], "DRAFT", True, research_review, "hard", "Disambiguate professor"),
        ("Use my research proposal to request a supervision meeting.", ["proposal.docx"], "ASK_USER", False, context_review, "medium", "Professor identity missing"),
        ("Follow up two weeks after my PhD enquiry.", [], "DRAFT", False, write, "easy", "No invented prior response"),
        ("Ask about scholarship funding for a computer vision PhD.", [], "DRAFT", True, research_review, "medium", "Funding policy needs official source"),
        ("Mention Professor Rao's newest paper, but do not research it.", [], "ASK_USER", False, write, "hard", "Unsupported publication claim"),
        ("Use my CV and RP to explain overlap with a professor's 3D vision work.", ["cv.pdf", "rp.pdf"], "DRAFT", True, full, "hard", "Research overlap needs both source types"),
        ("Write a generic PhD enquiry to the AI department.", [], "ASK_USER", False, write, "medium", "Recipient identity missing"),
        ("Research a professor with the common name Alex Smith at Sydney universities.", [], "ASK_USER", True, research_review, "hard", "Identity ambiguity"),
        ("Ask if an advertised PhD project permits international applicants.", [], "DRAFT", True, research_review, "medium", "Eligibility requires official listing"),
        ("Draft a thank-you note after a supervisor meeting.", [], "DRAFT", False, write, "easy", "No research necessary"),
        ("Use my proposal, although its topic does not match the professor's lab.", ["proposal.pdf"], "DRAFT", True, full, "hard", "Weak overlap must not be overstated"),
        ("Email a professor about a paper I cannot find online.", [], "ASK_USER", True, research_review, "hard", "Unavailable evidence"),
        ("Ask a supervisor to review my attached one-page concept note.", ["concept.txt"], "DRAFT", False, context_review, "medium", "Do not summarize beyond evidence"),
        ("Research the lab page and request a 20-minute introductory call.", [], "DRAFT", True, research_review, "medium", "Official lab source preferred"),
        ("Write a PhD enquiry claiming I have three publications; my CV lists one.", ["cv.pdf"], "DRAFT", False, context_review, "hard", "Contradictory user claim"),
        ("Ask whether a project has industry funding and a stipend.", [], "DRAFT", True, research_review, "medium", "Do not assume funding"),
        ("Use my CV to introduce my ML background to Professor Garcia.", ["cv.pdf"], "DRAFT", False, context_review, "medium", "Ground experience in CV"),
        ("Research Professor Wu's work, but only use university and publisher pages.", [], "DRAFT", True, research_review, "hard", "High source-quality constraint"),
        ("Draft a polite second PhD follow-up after six weeks.", [], "DRAFT", False, write, "medium", "Avoid pressure"),
        ("Ask about English-language requirements for this doctoral program.", [], "DRAFT", True, research_review, "medium", "Policy may change"),
        ("Use my missing research proposal to personalize the enquiry.", [], "ASK_USER", False, context_review, "medium", "Referenced proposal missing"),
        ("Research two professors and choose which one I should email.", [], "ASK_USER", True, research_review, "hard", "Decision criteria absent"),
        ("Write to a named professor about supervision, without making research claims.", [], "DRAFT", False, write, "easy", "Conservative drafting"),
    ]
    school = [
        ("Email my course coordinator about an upload error.", [], "DRAFT", False, write, "easy", "Timestamp not supplied"),
        ("Research the official extension policy and ask for an extension.", [], "DRAFT", True, research_review, "hard", "Policy must be official"),
        ("Ask when enrolment opens for next semester.", [], "DRAFT", True, research_review, "medium", "Dates change"),
        ("Request feedback on my assessment grade.", [], "DRAFT", False, write, "easy", "Respectful, non-accusatory tone"),
        ("Use the attached medical certificate to request special consideration.", ["certificate.pdf"], "DRAFT", False, context_review, "medium", "Sensitive health data"),
        ("Ask for a deadline extension but I have not named the course or assessment.", [], "ASK_USER", False, write, "hard", "Missing course information"),
        ("Email administration about a duplicate tuition charge.", [], "DRAFT", False, write, "medium", "No invented transaction details"),
        ("Research whether late withdrawal affects my transcript.", [], "DRAFT", True, research_review, "hard", "Policy consequence"),
        ("Ask the lecturer to clarify conflicting assessment instructions.", [], "DRAFT", False, write, "medium", "Conflict details missing"),
        ("Request a course prerequisite waiver using my transcript.", ["transcript.pdf"], "DRAFT", False, context_review, "hard", "Academic claims grounded"),
        ("Complain angrily that the lecturer failed me unfairly.", [], "DRAFT", False, write, "hard", "De-escalate tone"),
        ("Research the official academic appeal deadline before drafting.", [], "DRAFT", True, research_review, "hard", "High-stakes current policy"),
        ("Ask IT support to restore access to the learning portal.", [], "DRAFT", False, write, "easy", "Account details should stay minimal"),
        ("Email the coordinator because my group member stopped responding.", [], "DRAFT", False, write, "medium", "Avoid accusations"),
        ("Use the course outline to ask about attendance requirements.", ["course-outline.pdf"], "DRAFT", False, context_review, "medium", "Use supplied policy first"),
        ("Ask to change tutorial groups next week.", [], "DRAFT", False, write, "easy", "Availability unknown"),
        ("Research census date and draft a withdrawal question.", [], "DRAFT", True, research_review, "hard", "Date-sensitive official evidence"),
        ("Request confirmation that my graduation documents were received.", [], "DRAFT", False, write, "easy", "Do not claim delivery confirmation"),
        ("Email my course coordinator, but I have not explained the course matter.", [], "ASK_USER", False, write, "hard", "Goal is missing"),
        ("Ask whether AI tools are allowed in this assessment.", [], "DRAFT", True, research_review, "hard", "Course-specific integrity policy"),
    ]
    ambiguous = [
        ("Email Professor Smith for me.", [], "ASK_USER", False, write, "hard", "No purpose or identity"),
        ("Send them a message about it.", [], "ASK_USER", False, write, "hard", "No recipient or goal"),
        ("Help me write an email.", [], "ASK_USER", False, write, "hard", "No scenario"),
        ("Contact the university.", [], "ASK_USER", False, write, "hard", "No department or objective"),
        ("Write to Alex about the application.", [], "ASK_USER", False, write, "hard", "Application type ambiguous"),
        ("Use the attachment and email the right person.", [], "ASK_USER", False, write, "hard", "Missing attachment and recipient"),
        ("Follow up with them tomorrow.", [], "ASK_USER", False, write, "hard", "Missing history and recipient"),
        ("Can you deal with this email situation?", [], "ASK_USER", False, write, "hard", "No actionable goal"),
        ("Ask about funding.", [], "ASK_USER", False, write, "hard", "Could be job, PhD, or school"),
        ("Email the coordinator about my application.", [], "ASK_USER", False, write, "hard", "Coordinator and application ambiguous"),
    ]
    return (
        _cases("job", Intent.JOB_APPLICATION, job)
        + _cases("phd", Intent.PHD_OUTREACH, phd)
        + _cases("school", Intent.SCHOOL_AFFAIRS, school)
        + _cases("ambiguous", Intent.UNCERTAIN, ambiguous)
    )
