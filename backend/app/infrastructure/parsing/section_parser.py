import re

class JobSectionParser:
    """
    Section-Aware Job Description Parser.
    Segments raw job posting text into recognized functional sections based on standard headers,
    preserving exact source text evidence for grounding and downstream validation.
    """

    KNOWN_SECTION_PATTERNS = [
        ("REQUIRED_SKILLS", [
            r"required\s+key\s+skills",
            r"required\s+skills",
            r"mandatory\s+skills",
            r"key\s+skills",
            r"must\s+have\s+skills",
            r"must\s+have",
            r"core\s+requirements",
            r"required\s+qualifications",
            r"qualifications",
        ]),
        ("PREFERRED_SKILLS", [
            r"preferred\s+qualifications\s*&\s*skills",
            r"preferred\s+qualifications",
            r"preferred\s+skills",
            r"desired\s+skills",
            r"preferred\s+experience",
        ]),
        ("NICE_TO_HAVE_SKILLS", [
            r"good\s+to\s+have\s+knowledge",
            r"good\s+to\s+have",
            r"nice\s+to\s+have",
            r"bonus\s+skills",
            r"optional\s+skills",
        ]),
        ("RESPONSIBILITIES", [
            r"key\s+responsibilities",
            r"responsibilities",
            r"what\s+you'll\s+do",
            r"duties",
            r"role\s+overview",
        ]),
        ("EXPERIENCE", [
            r"experience\s+required",
            r"experience",
            r"years\s+of\s+experience",
        ]),
        ("EDUCATION", [
            r"education\s+required",
            r"education",
            r"academic\s+background",
        ]),
        ("CERTIFICATIONS", [
            r"certifications",
            r"licenses",
        ]),
        ("LOCATION_SCHEDULE", [
            r"work\s+location\s*&\s*schedule",
            r"location",
            r"work\s+mode",
        ]),
        ("ABOUT_COMPANY", [
            r"about\s+company",
            r"company\s-[#a-z0-9_-]+",
            r"about\s+us",
        ]),
    ]

    @classmethod
    def parse_sections(cls, text: str) -> dict[str, str]:
        """
        Parses job description into a dictionary mapping section keys to section text.
        Always includes 'FULL_TEXT' representing the raw un-altered job description.
        """
        if not text:
            return {"FULL_TEXT": ""}

        sections: dict[str, str] = {"FULL_TEXT": text}
        lines = text.split("\n")

        current_section = "GENERAL_SUMMARY"
        buffer: list[str] = []

        for line in lines:
            stripped = line.strip()
            # Check if line matches a known section header
            matched_header_key: str | None = None

            cleaned_header = re.sub(r"^[:\-\*#\s]+|[:\-\*#\s]+$", "", stripped).strip().lower()

            for sec_key, patterns in cls.KNOWN_SECTION_PATTERNS:
                for pat in patterns:
                    if re.fullmatch(pat, cleaned_header, re.IGNORECASE) or (
                        len(cleaned_header) < 50 and re.search(r"^" + pat + r"[:\s]*$", cleaned_header, re.IGNORECASE)
                    ):
                        matched_header_key = sec_key
                        break
                if matched_header_key:
                    break

            if matched_header_key:
                if buffer:
                    sections[current_section] = sections.get(current_section, "") + "\n" + "\n".join(buffer)
                    buffer = []
                current_section = matched_header_key
            else:
                buffer.append(line)

        if buffer:
            sections[current_section] = sections.get(current_section, "") + "\n" + "\n".join(buffer)

        return {k: v.strip() for k, v in sections.items() if v.strip()}
