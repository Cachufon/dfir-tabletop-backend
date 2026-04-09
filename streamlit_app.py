import streamlit as st
from datetime import datetime

st.set_page_config(page_title="DFIR TTX Platform", layout="wide")

SCENARIOS = {
    "Ransomware Attack": {
        "description": "A ransomware event has disrupted file access across critical systems. Leadership must make decisions under pressure across containment, communications, legal review, and recovery.",
        "injects": [
            {
                "title": "Inject 1: Initial Detection",
                "prompt": "Users report they cannot access shared files. A ransom note appears on multiple endpoints. What is your first move?",
                "options": [
                    "Isolate affected systems and activate incident response",
                    "Wait for more evidence before escalating",
                    "Pay the ransom immediately to restore operations",
                    "Ask IT to quietly investigate without formal activation"
                ],
                "best": "Isolate affected systems and activate incident response",
                "points": 10,
                "feedback": {
                    "Isolate affected systems and activate incident response": "Strong decision. This prioritizes containment and structured response.",
                    "Wait for more evidence before escalating": "Weak decision. Delay increases operational and business risk.",
                    "Pay the ransom immediately to restore operations": "Poor decision. This bypasses basic triage, legal review, and executive governance.",
                    "Ask IT to quietly investigate without formal activation": "Weak decision. Informal handling often leads to slow escalation and poor coordination."
                }
            },
            {
                "title": "Inject 2: Scope Expansion",
                "prompt": "The security team confirms multiple servers are impacted and backups may be at risk. What should leadership prioritize next?",
                "options": [
                    "Validate backup integrity, scope the incident, and preserve evidence",
                    "Focus only on restoring the loudest business unit first",
                    "Disconnect everything immediately with no coordination",
                    "Send a companywide message saying systems are safe"
                ],
                "best": "Validate backup integrity, scope the incident, and preserve evidence",
                "points": 10,
                "feedback": {
                    "Validate backup integrity, scope the incident, and preserve evidence": "Strong decision. This supports recovery confidence and investigation quality.",
                    "Focus only on restoring the loudest business unit first": "Weak decision. Recovery should be risk based, not noise based.",
                    "Disconnect everything immediately with no coordination": "Mixed decision. Containment matters, but uncoordinated disruption can create more damage.",
                    "Send a companywide message saying systems are safe": "Poor decision. Messaging must align to facts."
                }
            },
            {
                "title": "Inject 3: External Pressure",
                "prompt": "Threat actors claim they exfiltrated sensitive data and threaten public release. What is the best executive action?",
                "options": [
                    "Engage legal, privacy, communications, and incident leadership for coordinated response",
                    "Ignore the claim until the attackers post proof",
                    "Post a public statement immediately with no internal review",
                    "Negotiate directly with the threat actor without counsel"
                ],
                "best": "Engage legal, privacy, communications, and incident leadership for coordinated response",
                "points": 10,
                "feedback": {
                    "Engage legal, privacy, communications, and incident leadership for coordinated response": "Strong decision. This is the right cross functional response to exfiltration risk.",
                    "Ignore the claim until the attackers post proof": "Weak decision. This delays legal and regulatory preparedness.",
                    "Post a public statement immediately with no internal review": "Poor decision. Public communication must be deliberate and reviewed.",
                    "Negotiate directly with the threat actor without counsel": "Poor decision. This creates legal, regulatory, and strategic risk."
                }
            },
            {
                "title": "Inject 4: Recovery Decision",
                "prompt": "The business wants systems online fast, but the investigation is incomplete. What is the best recovery posture?",
                "options": [
                    "Use validated clean restore points and staged recovery with executive signoff",
                    "Restore everything as fast as possible regardless of validation",
                    "Delay all recovery until every forensic detail is complete",
                    "Let each business unit decide how to restore independently"
                ],
                "best": "Use validated clean restore points and staged recovery with executive signoff",
                "points": 10,
                "feedback": {
                    "Use validated clean restore points and staged recovery with executive signoff": "Strong decision. This balances speed, safety, and governance.",
                    "Restore everything as fast as possible regardless of validation": "Poor decision. Fast recovery without validation can reinfect the environment.",
                    "Delay all recovery until every forensic detail is complete": "Weak decision. Recovery and investigation must move in parallel where possible.",
                    "Let each business unit decide how to restore independently": "Poor decision. Recovery needs central coordination."
                }
            }
        ]
    }
}


def init_state():
    defaults = {
        "selected_scenario": "Ransomware Attack",
        "scenario_started": False,
        "current_inject": 0,
        "responses": [],
        "score": 0,
        "completed": False,
        "participant_name": "",
        "team_name": "",
        "start_time": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_scenario():
    st.session_state.scenario_started = False
    st.session_state.current_inject = 0
    st.session_state.responses = []
    st.session_state.score = 0
    st.session_state.completed = False
    st.session_state.start_time = None


def get_score_label(score, max_score):
    percentage = (score / max_score) * 100 if max_score else 0
    if percentage >= 90:
        return "Excellent"
    if percentage >= 75:
        return "Strong"
    if percentage >= 60:
        return "Moderate"
    return "Needs Improvement"


def render_home():
    st.title("DFIR Tabletop Exercise Platform")
    st.subheader("Test and validate cyber incident decision making in real time.")

    st.write(
        "This prototype simulates executive and incident response decision making during a cyber event. "
        "It is designed to demonstrate structured scenario flow, leadership choices, and after action results."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Scenario Type", "Cyber Crisis")

    with col2:
        st.metric("Exercise Format", "Decision Based")

    with col3:
        st.metric("Output", "Results Summary")

    st.markdown("### What this demo proves")
    st.write("A facilitator can run a scenario.")
    st.write("Participants can make decisions at each inject.")
    st.write("The platform captures responses and scores decision quality.")
    st.write("Results can be reviewed immediately after the exercise.")


def render_scenario():
    st.title("Scenario Simulation")

    scenario_name = st.selectbox("Select scenario", list(SCENARIOS.keys()), index=0)
    st.session_state.selected_scenario = scenario_name
    scenario = SCENARIOS[scenario_name]

    st.markdown("### Scenario Overview")
    st.write(scenario["description"])

    with st.expander("Participant setup", expanded=not st.session_state.scenario_started):
        st.session_state.participant_name = st.text_input(
            "Participant name",
            value=st.session_state.participant_name
        )
        st.session_state.team_name = st.text_input(
            "Team or function",
            value=st.session_state.team_name
        )

    col1, col2 = st.columns([1, 1])

    with col1:
        if not st.session_state.scenario_started:
            if st.button("Start Scenario", use_container_width=True):
                st.session_state.scenario_started = True
                st.session_state.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.rerun()

    with col2:
        if st.button("Reset Scenario", use_container_width=True):
            reset_scenario()
            st.rerun()

    if not st.session_state.scenario_started:
        st.info("Set participant details and start the scenario.")
        return

    inject_index = st.session_state.current_inject
    total_injects = len(scenario["injects"])

    if inject_index >= total_injects:
        st.session_state.completed = True
        st.success("Scenario complete. Go to Results to review performance.")
        return

    inject = scenario["injects"][inject_index]

    st.progress((inject_index + 1) / total_injects)
    st.caption(f"Inject {inject_index + 1} of {total_injects}")

    st.markdown(f"## {inject['title']}")
    st.write(inject["prompt"])

    response_key = f"inject_response_{inject_index}"
    selected_option = st.radio(
        "Choose your decision",
        inject["options"],
        key=response_key
    )

    if st.button("Submit Decision", use_container_width=True):
        is_best = selected_option == inject["best"]
        earned_points = inject["points"] if is_best else 0

        st.session_state.responses.append(
            {
                "inject_title": inject["title"],
                "prompt": inject["prompt"],
                "selected_option": selected_option,
                "best_option": inject["best"],
                "earned_points": earned_points,
                "max_points": inject["points"],
                "feedback": inject["feedback"][selected_option]
            }
        )

        st.session_state.score += earned_points
        st.session_state.current_inject += 1
        st.rerun()

    if st.session_state.responses:
        st.markdown("### Decisions submitted so far")
        for i, response in enumerate(st.session_state.responses, start=1):
            with st.expander(f"{i}. {response['inject_title']}"):
                st.write(f"**Your decision:** {response['selected_option']}")
                st.write(f"**Feedback:** {response['feedback']}")
                st.write(f"**Score:** {response['earned_points']} / {response['max_points']}")


def render_results():
    st.title("Results Dashboard")

    scenario = SCENARIOS[st.session_state.selected_scenario]
    max_score = sum(inject["points"] for inject in scenario["injects"])
    score = st.session_state.score
    rating = get_score_label(score, max_score)

    if not st.session_state.responses:
        st.warning("No scenario responses yet. Run the scenario first.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Score", f"{score} / {max_score}")

    with col2:
        st.metric("Performance", rating)

    with col3:
        st.metric("Injects Completed", f"{len(st.session_state.responses)} / {len(scenario['injects'])}")

    st.markdown("### Participant Summary")
    st.write(f"**Participant:** {st.session_state.participant_name or 'Not provided'}")
    st.write(f"**Team or function:** {st.session_state.team_name or 'Not provided'}")
    st.write(f"**Scenario:** {st.session_state.selected_scenario}")
    st.write(f"**Started:** {st.session_state.start_time or 'Not recorded'}")

    st.markdown("### Decision Review")

    for i, response in enumerate(st.session_state.responses, start=1):
        with st.container():
            st.markdown(f"#### {i}. {response['inject_title']}")
            st.write(f"**Prompt:** {response['prompt']}")
            st.write(f"**Your decision:** {response['selected_option']}")
            st.write(f"**Best practice choice:** {response['best_option']}")
            st.write(f"**Feedback:** {response['feedback']}")
            st.write(f"**Score:** {response['earned_points']} / {response['max_points']}")
            st.divider()

    st.markdown("### After Action Summary")

    strengths = []
    gaps = []

    for response in st.session_state.responses:
        if response["earned_points"] == response["max_points"]:
            strengths.append(response["inject_title"])
        else:
            gaps.append(response["inject_title"])

    if strengths:
        st.write("**Strengths observed:**")
        for item in strengths:
            st.write(f"• {item}")

    if gaps:
        st.write("**Improvement areas:**")
        for item in gaps:
            st.write(f"• {item}")

    if st.button("Download Summary Placeholder"):
        st.info("Next step: generate a downloadable after action report.")


def main():
    init_state()

    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Go to", ["Home", "Scenario", "Results"])

    if page == "Home":
        render_home()
    elif page == "Scenario":
        render_scenario()
    elif page == "Results":
        render_results()


if __name__ == "__main__":
    main()
