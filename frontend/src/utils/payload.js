const constantRubricpayload = {
  "Authenticity": {
    criteria_explanation: `Authenticity evaluates genuine engagement with cutting-edge technology and academic theory. This criterion assesses:
- Integration with current technological frameworks
- Novel contributions beyond state-of-art
- Implementation feasibility
- Industry/academic impact potential
The key question: "How does this work advance current technological or theoretical boundaries?"`,
    criteria_output: `1. Review technology integration (Be Critical):
 - Assess if current frameworks/tools are truly cutting-edge
 - List specific outdated technologies that should be replaced
 - Recommend modern alternatives
 - Identify missing integration points with industry standards
2. Analyze innovation level (Find Gaps):
 - Compare directly with top 3 competing solutions
 - Highlight specific areas lacking novelty
 - Recommend potential innovation directions
 - Suggest specific technical improvements
3. Evaluate impact potential (Be Realistic):
 - Challenge claimed benefits with market realities
 - Identify specific adoption barriers
 - Recommend concrete steps for increasing impact
 - List potential industry/academic partners`,
    score_explanation: `Score 1:
-Description: Uses outdated technologies/frameworks (pre-2020), no implementation details, lacks understanding of current state-of-art
-Examples: Relies on deprecated libraries, ignores modern frameworks, shows no technical depth
-Explanation: Fails to meet doctoral research standards
Score 2:
-Description: Uses basic current technologies without innovation
-Examples: Basic implementation of existing frameworks, no technical improvements, minimal integration
-Explanation: Shows limited technical understanding
Score 3:
-Description: Competent use of modern technologies
-Examples: Clear framework integration, basic technical improvements, viable implementation
-Explanation: Meets minimal doctoral standards
Score 4:
-Description: Advanced technological integration
-Examples: Optimized implementation, significant improvements to existing systems, novel combinations
-Explanation: Shows strong technical expertise
Score 5:
-Description: Revolutionary technological advancement
-Examples: Creates new technical paradigms, patent-worthy innovations, immediate industry impact
-Explanation: Publication-worthy technical contribution`
  },
  "Academic rigor": {
    criteria_explanation: `Academic rigor evaluates technical and methodological soundness. This criterion assesses:
- Experimental design validity
- Data collection/analysis methods
- Performance metrics
- Reproducibility standards
The key question: "How robust and reliable are the technical methods and results?"`,
    criteria_output: `1. Validate methodology (Be Thorough):
 - List specific statistical flaws
 - Identify missing validation steps
 - Recommend additional test cases
 - Suggest stronger validation methods
2. Examine technical implementation (Be Specific):
 - Highlight code quality issues
 - Identify performance bottlenecks
 - Recommend optimization strategies
 - Suggest specific refactoring approaches
3. Verify reproducibility (Be Strict):
 - List missing documentation
 - Identify dependencies issues
 - Recommend documentation improvements
 - Suggest containerization solutions`,
    score_explanation: `Score 1:
-Description: Invalid methodology, no statistical validation
-Examples: Inadequate sample size (n<30), missing error analysis, no validation sets
-Explanation: Fundamentally flawed approach
Score 2:
-Description: Basic methodology with significant gaps
-Examples: Simple t-tests only, limited cross-validation, poor error handling
-Explanation: Requires major methodological improvements
Score 3:
-Description: Valid but standard methodology
-Examples: Proper validation methods, adequate samples, clear metrics
-Explanation: Meets basic research standards
Score 4:
-Description: Advanced methodological approach
-Examples: Comprehensive validation, robust error handling, excellent documentation
-Explanation: Exceeds typical methodological standards
Score 5:
-Description: Groundbreaking methodological innovation
-Examples: Novel validation techniques, exceptional reproducibility, perfect implementation
-Explanation: Sets new methodological standards`
 },
  "Problem frame": {
    criteria_explanation: `Problem framing evaluates how the work addresses current technological or theoretical gaps. This criterion assesses:
- Technical/theoretical gap identification
- Market/academic need definition
- Scope and limitations
- Potential impact assessment
The key question: "Does this work address a significant, unresolved technical challenge?"`,
    criteria_output: `1. Assess gap analysis (Challenge Assumptions):
 - Question claimed limitations
 - Identify overlooked existing solutions
 - Recommend additional research areas
 - Suggest specific comparison studies
2. Examine scope (Be Realistic):
 - Highlight scope creep issues
 - Identify unrealistic assumptions
 - Recommend scope adjustments
 - Suggest specific boundary conditions
3. Evaluate impact (Be Critical):
 - Challenge impact claims
 - Identify adoption barriers
 - Recommend impact measurement methods
 - Suggest specific application domains`,
    score_explanation: `Score 1:
-Description: Addresses solved problem or trivial issue
-Examples: Solution exists in market, no technical challenge, irrelevant focus
-Explanation: Fails to justify research need
Score 2:
-Description: Minor technical improvement
-Examples: Slight optimization, limited application scope, minimal impact
-Explanation: Lacks significant contribution
Score 3:
-Description: Valid technical challenge
-Examples: Clear gap identified, reasonable scope, defined impact
-Explanation: Acceptable problem definition
Score 4:
-Description: Significant technical problem
-Examples: Major industry challenge, broad impact potential, clear value
-Explanation: Strong research justification
Score 5:
-Description: Critical unsolved challenge
-Examples: Industry-changing potential, massive impact, urgent need
-Explanation: Revolutionary problem identification`
  },
  "Problem-solving methodology": {
    criteria_explanation: `Evaluates technical approach and implementation strategy. This criterion examines:
- Technical solution design
- Implementation efficiency
- Resource optimization
- Scalability considerations
The key question: "How effective and efficient is the technical solution?"`,
    criteria_output: `1. Review technical approach (Find Weaknesses):
 - Identify architectural flaws
 - List potential failure points
 - Recommend alternative approaches
 - Suggest specific improvements
2. Analyze scalability (Be Practical):
 - Challenge scaling assumptions
 - Identify resource bottlenecks
 - Recommend optimization strategies
 - Suggest specific infrastructure improvements
3. Examine optimization (Be Thorough):
 - List inefficient components
 - Identify performance issues
 - Recommend specific optimizations
 - Suggest benchmarking approaches`,
    score_explanation: `Score 1:
-Description: Ineffective or impractical solution
-Examples: Unscalable design, excessive resource usage, critical flaws
-Explanation: Solution not viable
Score 2:
-Description: Basic solution with limitations
-Examples: Poor optimization, limited scalability, inefficient design
-Explanation: Needs major improvements
Score 3:
-Description: Functional technical solution
-Examples: Reasonable efficiency, basic scalability, adequate design
-Explanation: Meets minimum requirements
Score 4:
-Description: Optimized technical solution
-Examples: Excellent efficiency, good scalability, robust design
-Explanation: Strong technical implementation
Score 5:
-Description: Breakthrough solution
-Examples: Revolutionary efficiency, perfect scalability, optimal design
-Explanation: Sets new technical standards`
  },
  "Project outcome": {
    criteria_explanation: `Assesses technical achievements and practical impact. This criterion evaluates:
- Performance improvements
- Implementation completeness
- Technical innovations
- Practical applications
The key question: "What measurable improvements or innovations does this work deliver?"`,
    criteria_output: `1. Measure improvements (Be Objective):
 - Challenge performance claims
 - Identify measurement flaws
 - Recommend better metrics
 - Suggest comparative benchmarks
2. Evaluate completion (Be Critical):
 - List incomplete features
 - Identify quality issues
 - Recommend completion priorities
 - Suggest specific enhancements
3. Assess impact (Be Realistic):
 - Challenge adoption assumptions
 - Identify market barriers
 - Recommend go-to-market strategies
 - Suggest specific application domains`,
    score_explanation: `Score 1:
-Description: Failed to achieve goals
-Examples: No performance improvement, incomplete implementation, unusable results
-Explanation: Project unsuccessful
Score 2:
-Description: Minimal achievements
-Examples: <10% improvement, partial implementation, limited use cases
-Explanation: Poor outcome
Score 3:
-Description: Acceptable results
-Examples: 10-30% improvement, complete implementation, clear applications
-Explanation: Satisfactory outcome
Score 4:
-Description: Significant achievements
-Examples: 31-50% improvement, optimized implementation, broad impact
-Explanation: Strong results
Score 5:
-Description: Exceptional results
-Examples: >50% improvement, revolutionary implementation, immediate adoption
-Explanation: Outstanding achievement`
  },
  "Core concept": {
    criteria_explanation: `Evaluates fundamental technical innovation and theoretical advancement. This criterion assesses:
- Technical novelty
- Theoretical foundation
- Implementation architecture
- Innovation impact
The key question: "How innovative and sound is the core technical concept?"`,
    criteria_output: `1. Assess innovation (Challenge Claims):
 - Compare with existing patents
 - Identify derivative elements
 - Recommend differentiation strategies
 - Suggest unique applications
2. Examine architecture (Be Thorough):
 - List architectural weaknesses
 - Identify integration issues
 - Recommend structural improvements
 - Suggest specific design patterns
3. Evaluate foundation (Be Critical):
 - Challenge theoretical assumptions
 - Identify logical flaws
 - Recommend theoretical improvements
 - Suggest validation approaches`,
    score_explanation: `Score 1:
-Description: Derivative or flawed concept
-Examples: Copies existing solution, fundamental misunderstandings, invalid approach
-Explanation: Fails conceptually
Score 2:
-Description: Basic concept with flaws
-Examples: Minor modifications to existing work, weak theoretical base, limited innovation
-Explanation: Needs conceptual revision
Score 3:
-Description: Sound technical concept
-Examples: Clear innovation, valid theory, reasonable approach
-Explanation: Acceptable concept
Score 4:
-Description: Strong technical innovation
-Examples: Significant advances, excellent theory, novel approach
-Explanation: Outstanding concept
Score 5:
-Description: Revolutionary concept
-Examples: Breakthrough innovation, paradigm-shifting theory, patentable idea
-Explanation: Field-changing concept`
  }
};

const businessRubricpayload = {
  "Relevance and Practical Impact": {
    criteria_explanation: `
      Evaluates the project's alignment with industry needs and real-world applicability. Assesses potential benefits and improvements for businesses or organizations.
      1. Confirm that the problem addresses a relevant business need or gap.
      2. Evaluate if the project offers feasible, actionable recommendations.
      3. Challenge claims about impact with practical, industry-relevant evidence.
    `,
    criteria_output: `
      1. Evaluate Problem Relevance: Confirm that the problem addresses a relevant business need or gap.
      2. Assess Real-World Applicability: Evaluate if the project offers feasible, actionable recommendations.
      3. Analyze Impact Potential: Challenge claims about impact with practical, industry-relevant evidence.
    `,
    score_explanation: `
      Score 1: Irrelevant problem with no practical application.
      Score 2: Basic relevance with limited applicability.
      Score 3: Clear relevance and practical implications.
      Score 4: Strong, actionable insights with potential industry impact.
      Score 5: Highly impactful, with immediate and valuable applications.
    `
  },
  "Analytical Rigor and Methodological Soundness": {
    criteria_explanation: `
      Assesses the thoroughness and accuracy of the project's analysis, including data quality and validity of findings.
      1. Identify any methodological weaknesses or assumptions.
      2. Assess data sources and consistency, and suggest improvements.
      3. Ensure conclusions are well-supported by data.
    `,
    criteria_output: `
      1. Validate Analytical Approach: Identify any methodological weaknesses or assumptions.
      2. Examine Data Quality and Analysis: Assess data sources and consistency, and suggest improvements.
      3. Verify Soundness of Conclusions: Ensure conclusions are well-supported by data.
    `,
    score_explanation: `
      Score 1: Flawed methodology, unreliable results.
      Score 2: Basic methodology with significant gaps.
      Score 3: Standard methodology, reliable insights.
      Score 4: Thorough analysis with strong, well-supported insights.
      Score 5: Exceptionally rigorous, data-driven conclusions.
    `
  },
  "Problem Framing and Business Context": {
    criteria_explanation: `
      Evaluates clarity in defining the business problem, scope, and understanding of industry context.
      1. Confirm that the problem is well-defined and relevant.
      2. Identify if the project’s scope is appropriate and achievable.
      3. Ensure understanding of relevant market or industry context.
    `,
    criteria_output: `
      1. Evaluate Problem Definition: Confirm that the problem is well-defined and relevant.
      2. Examine Scope and Feasibility: Identify if the project’s scope is appropriate and achievable.
      3. Contextualize with Market Insights: Ensure understanding of relevant market or industry context.
    `,
    score_explanation: `
      Score 1: Poorly defined problem, lacking business relevance.
      Score 2: General problem with limited context.
      Score 3: Well-defined problem with business context.
      Score 4: Strong framing with market insights.
      Score 5: Expertly framed, with deep business context understanding.
    `
  },
  "Problem-Solving Approach and Strategic Insight": {
    criteria_explanation: `
      Evaluates the project's approach to solving the business problem, including strategic thinking and feasibility.
      1. Evaluate use of business frameworks (e.g., SWOT, PESTLE).
      2. Challenge solutions that may lack feasibility.
      3. Identify any limitations in resources or implementation.
    `,
    criteria_output: `
      1. Assess Strategic Thinking: Evaluate use of business frameworks (e.g., SWOT, PESTLE).
      2. Examine Solution Feasibility: Challenge solutions that may lack feasibility.
      3. Consider Practical Constraints: Identify any limitations in resources or implementation.
    `,
    score_explanation: `
      Score 1: Ineffective approach with limited strategic value.
      Score 2: Basic approach with feasibility issues.
      Score 3: Competent strategy with actionable recommendations.
      Score 4: Strong, well-grounded strategy.
      Score 5: Highly strategic and innovative approach with practical value.
    `
  },
  "Project Outcomes and Business Implications": {
    criteria_explanation: `
      Assesses the project's practical outcomes and implications for business practice, including clarity of recommendations.
      1. Assess if recommendations are actionable and achievable.
      2. Evaluate expected benefits for the business.
      3. Identify any gaps or incomplete areas.
    `,
    criteria_output: `
      1. Evaluate Practical Recommendations: Assess if recommendations are actionable and achievable.
      2. Analyze Potential Business Benefits: Evaluate expected benefits for the business.
      3. Assess Completeness of Solution: Identify any gaps or incomplete areas.
    `,
    score_explanation: `
      Score 1: No meaningful outcomes, impractical recommendations.
      Score 2: Minimal outcomes with limited relevance.
      Score 3: Clear, practical recommendations with relevance.
      Score 4: Strong outcomes with significant business value.
      Score 5: Outstanding outcomes with transformative implications.
    `
  },
  "Innovation and Contribution to Knowledge": {
    criteria_explanation: `
      Evaluates originality and contribution to the field, including uniqueness of insights and broader applicability.
      1. Challenge originality by identifying overlap with existing solutions and highlighting unique value.
      2. Assess contribution to business knowledge by evaluating the project’s impact on business practices.
      3. Consider broader applicability by assessing if solutions could apply across different contexts.
    `,
    criteria_output: `
      1. Challenge Originality: Identify overlap with existing solutions and highlight unique value.
      2. Assess Contribution to Business Knowledge: Evaluate the project’s contribution to business practices.
      3. Consider Broader Application: Assess if solutions could apply across different contexts.
    `,
    score_explanation: `
      Score 1: Minimal contribution, redundant ideas.
      Score 2: Limited originality, minor practical contribution.
      Score 3: Useful insights with moderate innovation.
      Score 4: Significant, unique contribution to business knowledge.
      Score 5: Highly original, with potential to influence business practices broadly.
    `
  }
};


export default {constantRubricpayload,businessRubricpayload};