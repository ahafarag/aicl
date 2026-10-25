"""Stock phrases that are over-represented in instruction-tuned LLM output.

This list is a heuristic, not evidence of authorship: every entry is ordinary
English that people also write. It is useful for spotting filler and cliché
during editing. Entries are regular expressions matched case-insensitively on
word boundaries. Contributions should cite a corpus comparison where possible.
"""

STOCK_PHRASES: dict[str, list[str]] = {
    "vocabulary": [
        r"delv(?:e|es|ed|ing)",
        r"tapestr(?:y|ies)",
        r"testament to",
        r"realm(?:s)?",
        r"multifaceted",
        r"intricac(?:y|ies)",
        r"intricate",
        r"pivotal",
        r"underscor(?:e|es|ed|ing)",
        r"showcas(?:e|es|ed|ing)",
        r"seamless(?:ly)?",
        r"ever-evolving",
        r"meticulous(?:ly)?",
        r"bustling",
        r"vibrant",
        r"embark(?:s|ed|ing)? on",
        r"foster(?:s|ed|ing)?",
        r"harness(?:es|ed|ing)? the power",
        r"unlock(?:s|ed|ing)? the (?:full )?potential",
        r"navigat(?:e|es|ed|ing) the (?:complexities|landscape|challenges)",
        r"(?:digital|evolving|ever-changing|complex) landscape",
        r"game[- ]changer",
        r"paradigm shift",
    ],
    "framing": [
        r"in today's (?:fast-paced|digital|modern|ever-changing) (?:world|age|landscape)",
        r"it(?:'s| is) (?:important|worth|crucial) to (?:note|remember|mention|consider)",
        r"it(?:'s| is) not (?:just|only|merely) (?:about )?\w+[^.]{0,40}?(?:it(?:'s| is)|but)",
        r"plays? a (?:crucial|pivotal|vital|key|significant) role",
        r"(?:a|an) (?:rich|complex|diverse) (?:tapestry|array|mosaic)",
        r"whether you(?:'re| are) an? \w+ or an? \w+",
        r"at the end of the day",
        r"when it comes to",
    ],
    "transitions": [
        r"furthermore",
        r"moreover",
        r"additionally",
        r"in conclusion",
        r"in summary",
        r"ultimately",
        r"overall",
        r"that being said",
    ],
}
