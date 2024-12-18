const constantRubric = {
    "Authenticity": {
        "criteria_explanation": 
        `Authenticity evaluates genuine engagement with cutting-edge technology and academic theory. This criterion assesses:
        - Integration with current technological frameworks
        - Novel contributions beyond state-of-art
        - Implementation feasibility
        - Industry/academic impact potential
        The key question: "How does this work advance current technological or theoretical boundaries?"`,
        
        "criteria_output": {
            "1. Review technology integration (Be Critical)": `Assess if current frameworks/tools are truly cutting-edge, list specific outdated technologies that should be replaced, recommend modern alternatives, and identify missing integration points with industry standards.`,
            "2. Analyze innovation level (Find Gaps)": `Compare directly with top 3 competing solutions, highlight specific areas lacking novelty, recommend potential innovation directions, and suggest specific technical improvements.`,
            "3. Evaluate impact potential (Be Realistic)": `Challenge claimed benefits with market realities, identify specific adoption barriers, recommend concrete steps for increasing impact, and list potential industry/academic partners.`
        },

        "score_explanation": {
            "Score 1": {
                "Description": `Uses outdated technologies/frameworks (pre-2020), no implementation details, lacks understanding of current state-of-art`,
                "Examples": `Relies on deprecated libraries, ignores modern frameworks, shows no technical depth`,
                "Explanation": `Fails to meet doctoral research standards`
            },
            "Score 2": {
                "Description": `Uses basic current technologies without innovation`,
                "Examples": `Basic implementation of existing frameworks, no technical improvements, minimal integration`,
                "Explanation": `Shows limited technical understanding`
            },
            "Score 3": {
                "Description": `Competent use of modern technologies`,
                "Examples": `Clear framework integration, basic technical improvements, viable implementation`,
                "Explanation": `Meets minimal doctoral standards`
            },
            "Score 4": {
                "Description": `Advanced technological integration`,
                "Examples": `Optimized implementation, significant improvements to existing systems, novel combinations`,
                "Explanation": `Shows strong technical expertise`
            },
            "Score 5": {
                "Description": `Revolutionary technological advancement`,
                "Examples": `Creates new technical paradigms, patent-worthy innovations, immediate industry impact`,
                "Explanation": `Publication-worthy technical contribution`
            }
        }
    },
    "Academic rigor": {
        "criteria_explanation": 
        `Academic rigor evaluates technical and methodological soundness. This criterion assesses:
        - Experimental design validity
        - Data collection/analysis methods
        - Performance metrics
        - Reproducibility standards
        The key question: "How robust and reliable are the technical methods and results?"`,
        
        "criteria_output": {
            "1. Verify experimental design": `Examine the design's validity and identify potential biases, oversights, or design flaws. Suggest alternative approaches for stronger validity.`,
            "2. Assess data handling (accuracy and relevance)": `Evaluate the appropriateness of data collection, cleaning, and analysis methods. Suggest improvements for better data integrity.`,
            "3. Evaluate performance metrics": `Review if metrics are suitable for measuring outcomes, and propose alternative metrics if current ones do not capture key performance aspects.`
        },

        "score_explanation": {
            "Score 1": {
                "Description": `Lacks methodological rigor, does not address biases or validity of methods`,
                "Examples": `Random sampling errors, inappropriate metrics, insufficient data analysis depth`,
                "Explanation": `Methodology is unacceptable for academic research`
            },
            "Score 2": {
                "Description": `Basic methodology with limited rigor`,
                "Examples": `Simplistic design, misses minor biases, uses adequate but uninspired metrics`,
                "Explanation": `Falls below the expected standard of rigor`
            },
            "Score 3": {
                "Description": `Acceptable rigor with room for improvement`,
                "Examples": `Reasonable methodological foundation, basic performance metrics, limited bias control`,
                "Explanation": `Meets minimum academic standards`
            },
            "Score 4": {
                "Description": `Strong methodology with clear rigor`,
                "Examples": `Thoughtful design, avoids major biases, thorough use of relevant metrics`,
                "Explanation": `Reflects a strong understanding of methodological principles`
            },
            "Score 5": {
                "Description": `Exceptional methodological rigor`,
                "Examples": `Innovative design, full bias control, excellent metric selection`,
                "Explanation": `Sets a high standard for academic research rigor`
            }
        }
    },
    "Problem Frame": {
        "criteria_explanation": 
        `Problem Frame assesses the clarity, relevance, and importance of the problem statement. This criterion evaluates:
        - Problem clarity and articulation
        - Relevance to current research/industry challenges
        - Potential impact of solving the problem
        The key question: "How well is the problem defined and contextualized?"`,
        
        "criteria_output": {
            "1. Clarify problem statement": `Assess the clarity and relevance of the problem, suggest improvements for a sharper focus.`,
            "2. Contextualize with industry/research needs": `Analyze how the problem aligns with current industry or academic priorities, suggest adjustments for alignment.`,
            "3. Impact assessment": `Evaluate the potential impact of solving the problem, and suggest ways to enhance its relevance or importance.`
        },

        "score_explanation": {
            "Score 1": {
                "Description": `Problem statement is vague, lacks relevance`,
                "Examples": `Unfocused problem, no clear objectives, outdated context`,
                "Explanation": `Fails to identify a meaningful research issue`
            },
            "Score 2": {
                "Description": `Basic but limited problem framing`,
                "Examples": `General problem with minimal context, lacks depth`,
                "Explanation": `Identifies an issue but without significant insight`
            },
            "Score 3": {
                "Description": `Well-defined problem with clear context`,
                "Examples": `Clear problem statement, some relevant context provided`,
                "Explanation": `Adequate foundation for research`
            },
            "Score 4": {
                "Description": `Strong problem framing with relevant context`,
                "Examples": `Detailed problem definition, relevant academic/industry context`,
                "Explanation": `Well-prepared for in-depth research`
            },
            "Score 5": {
                "Description": `Exceptional problem framing with high relevance`,
                "Examples": `Problem clearly addresses a key gap, significant academic or industry relevance`,
                "Explanation": `Highly impactful research potential`
            }
        }
    },
    "Problem-Solving Methodology": {
        "criteria_explanation": 
        `Problem-Solving Methodology evaluates the soundness and feasibility of the chosen methods to address the problem. This criterion assesses:
        - Method selection and justification
        - Feasibility and implementation
        - Consistency with the problem frame
        The key question: "Are the chosen methods appropriate for solving the defined problem?"`,
        
        "criteria_output": {
            "1. Justify method choice": `Evaluate if the selected methods are well-justified and aligned with the problem requirements.`,
            "2. Assess feasibility": `Review the practical feasibility of the proposed methods and suggest necessary modifications.`,
            "3. Consistency with problem statement": `Ensure that methods align with the stated problem's complexity and scope.`
        },

        "score_explanation": {
            "Score 1": {
                "Description": `Inappropriate methods with no justification`,
                "Examples": `Random selection of methods, no logical link to problem`,
                "Explanation": `Methods fail to address the problem`
            },
            "Score 2": {
                "Description": `Basic methods with limited justification`,
                "Examples": `Simplistic approach, lacks depth or alignment`,
                "Explanation": `Minimal alignment with problem requirements`
            },
            "Score 3": {
                "Description": `Appropriate methodology with some justification`,
                "Examples": `Reasonable method choice, basic feasibility assessment`,
                "Explanation": `Sufficient for basic problem-solving`
            },
            "Score 4": {
                "Description": `Well-justified methodology, feasible and aligned`,
                "Examples": `Sound method choice, good feasibility, logical consistency`,
                "Explanation": `Appropriate approach to solve the problem`
            },
            "Score 5": {
                "Description": `Innovative, well-justified methodology`,
                "Examples": `Strong alignment, feasibility, unique approach`,
                "Explanation": `Exceptional methodological rigor and innovation`
            }
        }
    },
    "Project Outcome": {
        "criteria_explanation": 
        `Project Outcome evaluates the significance and quality of the final results. This criterion assesses:
        - Achievement of objectives
        - Contribution to knowledge or practice
        - Limitations and future work potential
        The key question: "Does the outcome deliver value and further knowledge?"`,
        
        "criteria_output": {
            "1. Evaluate achievement of objectives": `Assess if project objectives were met and analyze areas of improvement.`,
            "2. Analyze contribution": `Evaluate how well the outcome contributes to existing knowledge or practical applications.`,
            "3. Identify limitations and suggest future work": `Provide insights into potential limitations and directions for future research or practical improvements.`
        },

        "score_explanation": {
            "Score 1": {
                "Description": `Does not achieve stated objectives, lacks contribution`,
                "Examples": `Outcome falls short of objectives, no significant findings`,
                "Explanation": `Minimal value`
            },
            "Score 2": {
                "Description": `Basic outcome with minimal contributions`,
                "Examples": `Limited findings, modest practical implications`,
                "Explanation": `Below the expected outcome`
            },
            "Score 3": {
                "Description": `Adequate outcome with some contributions`,
                "Examples": `Basic achievement of objectives, minor contributions`,
                "Explanation": `Meets minimum standards`
            },
            "Score 4": {
                "Description": `Good outcome with significant contributions`,
                "Examples": `Clear achievement of objectives, practical/academic contributions`,
                "Explanation": `Strong outcome`
            },
            "Score 5": {
                "Description": `Exceptional outcome with breakthrough contributions`,
                "Examples": `Major findings, significant practical implications`,
                "Explanation": `Sets a new standard in the field`
            }
        }
    },
    "Core Concept": {
        "criteria_explanation": 
        `Core Concept assesses the originality and conceptual robustness of the work. This criterion evaluates:
        - Uniqueness of the concept
        - Alignment with identified needs
        - Potential to inspire future work or innovations
        The key question: "Does the core concept provide a unique and compelling foundation?"`,
        
        "criteria_output": {
            "1. Assess originality": `Evaluate the novelty and distinctiveness of the core concept and identify any closely related existing concepts.`,
            "2. Determine relevance to needs": `Examine the alignment with the practical or theoretical needs it intends to address.`,
            "3. Evaluate potential to inspire": `Assess the potential to stimulate future research or applications.`
        },

        "score_explanation": {
            "Score 1": {
                "Description": `Concept lacks originality, minimal impact`,
                "Examples": `Rehashes known ideas with no new angle`,
                "Explanation": `Little to no conceptual contribution`
            },
            "Score 2": {
                "Description": `Limited originality, minor differentiation`,
                "Examples": `Marginally different from existing work, limited new insights`,
                "Explanation": `Minor conceptual advancement`
            },
            "Score 3": {
                "Description": `Moderate originality, reasonably aligned with needs`,
                "Examples": `Slightly innovative, addresses needs adequately`,
                "Explanation": `Meets basic expectations`
            },
            "Score 4": {
                "Description": `Clear originality with strong alignment`,
                "Examples": `Noticeably different from current concepts, significant relevance`,
                "Explanation": `Substantial conceptual contribution`
            },
            "Score 5": {
                "Description": `Exceptional originality, groundbreaking concept`,
                "Examples": `Highly unique, pioneering concept with wide-ranging impact`,
                "Explanation": `Sets a new benchmark for originality`
            }
        }
    }
};

const businessRubric = {
    "Relevance and Practical Impact": {
        "criteria_explanation": `
        Evaluates the project's alignment with industry needs and real-world applicability. Assesses potential benefits and improvements for businesses or organizations.
        - Confirm that the problem addresses a relevant business need or gap.
        - Evaluate if the project offers feasible, actionable recommendations.
        - Challenge claims about impact with practical, industry-relevant evidence.
        The key question: "Does the project address a relevant business need and offer practical, actionable insights?"
        `,
        "criteria_output": {
            "Evaluate Problem Relevance": "Confirm that the problem addresses a relevant business need or gap.",
            "Assess Real-World Applicability": "Evaluate if the project offers feasible, actionable recommendations.",
            "Analyze Impact Potential": "Challenge claims about impact with practical, industry-relevant evidence."
        },
        "score_explanation": {
            "Score 1": {
                "Description": "Irrelevant problem with no practical application.",
                "Examples": "A project that solves a non-existent problem or lacks any connection to real-world scenarios.",
                "Explanation": "The project does not align with industry needs or offer practical benefits."
            },
            "Score 2": {
                "Description": "Basic relevance with limited applicability.",
                "Examples": "Addresses a minor issue but offers limited scope for practical implementation.",
                "Explanation": "The project identifies a real-world issue but lacks depth in applicability."
            },
            "Score 3": {
                "Description": "Clear relevance and practical implications.",
                "Examples": "A project that solves a common business problem with some actionable insights.",
                "Explanation": "The project aligns well with industry needs and offers practical outcomes."
            },
            "Score 4": {
                "Description": "Strong, actionable insights with potential industry impact.",
                "Examples": "Provides robust solutions that are ready for implementation in business contexts.",
                "Explanation": "The project has clear, practical recommendations and industry relevance."
            },
            "Score 5": {
                "Description": "Highly impactful, with immediate and valuable applications.",
                "Examples": "Addresses a critical business issue with highly actionable, innovative solutions.",
                "Explanation": "The project offers exceptional relevance and practical benefits for the industry."
            }
        }
    },
    "Analytical Rigor and Methodological Soundness": {
        "criteria_explanation": `
        Assesses the thoroughness and accuracy of the project's analysis, including data quality and validity of findings.
        - Identify any methodological weaknesses or assumptions.
        - Assess data sources and consistency, and suggest improvements.
        - Ensure conclusions are well-supported by data.
        The key question: "Is the project's analysis rigorous, and are its conclusions well-supported by reliable data?"
        `,
        "criteria_output": {
            "Validate Analytical Approach": "Identify any methodological weaknesses or assumptions.",
            "Examine Data Quality and Analysis": "Assess data sources and consistency, and suggest improvements.",
            "Verify Soundness of Conclusions": "Ensure conclusions are well-supported by data."
        },
        "score_explanation": {
            "Score 1": {
                "Description": "Flawed methodology, unreliable results.",
                "Examples": "Analysis based on biased or insufficient data.",
                "Explanation": "The findings cannot be trusted due to poor analytical practices."
            },
            "Score 2": {
                "Description": "Basic methodology with significant gaps.",
                "Examples": "Uses some data but lacks rigor in analysis.",
                "Explanation": "The approach provides insights but is not sufficiently thorough."
            },
            "Score 3": {
                "Description": "Standard methodology, reliable insights.",
                "Examples": "Applies common analytical techniques with dependable outcomes.",
                "Explanation": "The analysis is reliable but lacks advanced rigor."
            },
            "Score 4": {
                "Description": "Thorough analysis with strong, well-supported insights.",
                "Examples": "Comprehensive evaluation leading to robust conclusions.",
                "Explanation": "The methodology is well-structured and produces strong insights."
            },
            "Score 5": {
                "Description": "Exceptionally rigorous, data-driven conclusions.",
                "Examples": "Applies advanced methods with highly reliable findings.",
                "Explanation": "The analysis is exemplary, with conclusions backed by high-quality data."
            }
        }
    },
    "Problem Framing and Business Context": {
        "criteria_explanation": `
        Evaluates clarity in defining the business problem, scope, and understanding of industry context.
        - Confirm that the problem is well-defined and relevant.
        - Identify if the project’s scope is appropriate and achievable.
        - Ensure understanding of relevant market or industry context.
        The key question: "Is the business problem well-defined, and does the project demonstrate an understanding of its industry context?"
        `,
        "criteria_output": {
            "Evaluate Problem Definition": "Confirm that the problem is well-defined and relevant.",
            "Examine Scope and Feasibility": "Identify if the project’s scope is appropriate and achievable.",
            "Contextualize with Market Insights": "Ensure understanding of relevant market or industry context."
        },
        "score_explanation": {
            "Score 1": {
                "Description": "Poorly defined problem, lacking business relevance.",
                "Examples": "A vague or irrelevant problem statement with no clear context.",
                "Explanation": "The project fails to establish a meaningful business problem."
            },
            "Score 2": {
                "Description": "General problem with limited context.",
                "Examples": "An average problem definition with little focus on business impact.",
                "Explanation": "The project touches on a relevant problem but lacks detail."
            },
            "Score 3": {
                "Description": "Well-defined problem with business context.",
                "Examples": "Clearly identifies a problem and its business relevance.",
                "Explanation": "The problem is well-articulated, with a clear connection to industry needs."
            },
            "Score 4": {
                "Description": "Strong framing with market insights.",
                "Examples": "Defines a specific issue with supporting market research or context.",
                "Explanation": "The project is grounded in real-world business scenarios."
            },
            "Score 5": {
                "Description": "Expertly framed, with deep business context understanding.",
                "Examples": "Delivers a compelling problem definition backed by comprehensive industry insights.",
                "Explanation": "The project is a standout example of problem definition and business relevance."
            }
        }
    },
    "Problem-Solving Approach and Strategic Insight": {
        "criteria_explanation": `
        Evaluates the project's approach to solving the business problem, including strategic thinking and feasibility.
        - Evaluate use of business frameworks (e.g., SWOT, PESTLE).
        - Challenge solutions that may lack feasibility.
        - Identify any limitations in resources or implementation.
        The key question: "Is the project's problem-solving approach strategic, feasible, and practical?"
        `,
        "criteria_output": {
            "Assess Strategic Thinking": "Evaluate use of business frameworks (e.g., SWOT, PESTLE).",
            "Examine Solution Feasibility": "Challenge solutions that may lack feasibility.",
            "Consider Practical Constraints": "Identify any limitations in resources or implementation."
        },
        "score_explanation": {
            "Score 1": {
                "Description": "Ineffective approach with limited strategic value.",
                "Examples": "Random, unstructured solutions with no strategic basis.",
                "Explanation": "The approach lacks direction and practical relevance."
            },
            "Score 2": {
                "Description": "Basic approach with feasibility issues.",
                "Examples": "Proposes ideas that are hard to implement or poorly thought through.",
                "Explanation": "The strategy has potential but requires significant refinement."
            },
            "Score 3": {
                "Description": "Competent strategy with actionable recommendations.",
                "Examples": "Proposes solid strategies that are ready for practical use.",
                "Explanation": "The approach is sound and focuses on solving the problem effectively."
            },
            "Score 4": {
                "Description": "Strong, well-grounded strategy.",
                "Examples": "Provides clear, achievable solutions grounded in analysis.",
                "Explanation": "The approach is strategic and practical, delivering meaningful recommendations."
            },
            "Score 5": {
                "Description": "Highly strategic and innovative approach with practical value.",
                "Examples": "Combines innovative thinking with feasible, strategic solutions.",
                "Explanation": "The project excels in delivering impactful, strategic insights."
            }
        }
    },
    "Project Outcomes and Business Implications": {
        "criteria_explanation": `
        Assesses the project's practical outcomes and implications for business practice, including clarity of recommendations.
        - Assess if recommendations are actionable and achievable.
        - Evaluate expected benefits for the business.
        - Identify any gaps or incomplete areas.
        The key question: "Are the project outcomes practical, complete, and beneficial for business practice?"
        `,
        "criteria_output": {
            "Evaluate Practical Recommendations": "Assess if recommendations are actionable and achievable.",
            "Analyze Potential Business Benefits": "Evaluate expected benefits for the business.",
            "Assess Completeness of Solution": "Identify any gaps or incomplete areas."
        },
        "score_explanation": {
            "Score 1": {
                "Description": "No meaningful outcomes, impractical recommendations.",
                "Examples": "Fails to deliver actionable solutions or demonstrate value.",
                "Explanation": "The project lacks practical relevance and completeness."
            },
            "Score 2": {
                "Description": "Minimal outcomes with limited relevance.",
                "Examples": "Offers some value but lacks significant depth or insight.",
                "Explanation": "The outcomes are incomplete or lack relevance to business needs."
            },
            "Score 3": {
                "Description": "Clear, practical recommendations with relevance.",
                "Examples": "Proposes useful solutions with business value.",
                "Explanation": "The project meets the expectations of practical relevance."
            },
            "Score 4": {
                "Description": "Strong outcomes with significant business value.",
                "Examples": "Delivers actionable and well-thought-out recommendations.",
                "Explanation": "The outcomes are practical, complete, and highly beneficial."
            },
            "Score 5": {
                "Description": "Outstanding outcomes with transformative implications.",
                "Examples": "Proposes groundbreaking solutions that can transform business practices.",
                "Explanation": "The project demonstrates exceptional impact and practicality."
            }
        }
    },
    "Innovation and Contribution to Knowledge": {
        "criteria_explanation": `
        Evaluates originality and contribution to the field, including uniqueness of insights and broader applicability.
        - Challenge Originality: Identify overlap with existing solutions, highlight unique value.
        - Assess Contribution to Business Knowledge: Evaluate the project’s contribution to business practices.
        - Consider Broader Application: Assess if solutions could apply across different contexts.
        The key question: "How original is the project, and what is its contribution to advancing business knowledge?"
        `,
        "criteria_output": {
            "Challenge Originality": "Identify overlap with existing solutions, highlight unique value.",
            "Assess Contribution to Business Knowledge": "Evaluate the project’s contribution to business practices.",
            "Consider Broader Application": "Assess if solutions could apply across different contexts."
        },
        "score_explanation": {
            "Score 1": {
                "Description": "Minimal contribution, redundant ideas.",
                "Examples": "The project largely repeats existing solutions without offering new perspectives.",
                "Explanation": "The project lacks originality and offers little new value to the field."
            },
            "Score 2": {
                "Description": "Limited originality, minor practical contribution.",
                "Examples": "The project introduces a few new ideas but is largely derivative.",
                "Explanation": "The project offers limited innovation and has only minor relevance to business practices."
            },
            "Score 3": {
                "Description": "Useful insights with moderate innovation.",
                "Examples": "The project offers some new perspectives and actionable insights, though it remains grounded in existing solutions.",
                "Explanation": "The project contributes useful insights and moderately advances the field of business knowledge."
            },
            "Score 4": {
                "Description": "Significant, unique contribution to business knowledge.",
                "Examples": "The project introduces fresh, impactful ideas that contribute significantly to the field.",
                "Explanation": "The project offers a substantial, unique contribution to business practices and knowledge."
            },
            "Score 5": {
                "Description": "Highly original, with potential to influence business practices broadly.",
                "Examples": "The project is groundbreaking, with the potential to shape business practices across industries.",
                "Explanation": "The project is highly original, offering innovative solutions with broad applicability and transformative potential."
            }
        }
    }

};

export default {businessRubric, constantRubric};




