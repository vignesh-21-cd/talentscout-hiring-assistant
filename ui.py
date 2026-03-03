"""
TalentScout Hiring Assistant — UI styling and layout helpers.
All custom CSS, styled sections, and layout wrappers live here.
"""
import html
import streamlit as st

# ---------------------------------------------------------------------------
# Global styles
# ---------------------------------------------------------------------------

def apply_global_styles() -> None:
    """Inject custom CSS for background, typography, chat spacing, and cards."""
    st.markdown(
        """
        <style>
        /* Soft background */
        .stApp { background-color: #f5f7fa; }
        /* Main content: max-width and center */
        .block-container { padding: 1.5rem 2rem; max-width: 1000px; margin-left: auto; margin-right: auto; }
        /* Header area (centered) */
        .header-area { text-align: center; margin-bottom: 0.5rem; }
        .header-area h1 { font-size: 1.85rem !important; font-weight: 600 !important; margin-bottom: 0.2rem !important; }
        .header-subtitle { font-size: 0.95rem; color: #4b5563; margin-top: 0.15rem; margin-bottom: 0; }
        /* Section headers */
        h2 { font-size: 1.25rem !important; font-weight: 600 !important; margin-top: 1rem !important; }
        h3 { font-size: 1.1rem !important; font-weight: 600 !important; margin-top: 0.75rem !important; }
        /* Mode badge */
        .mode-badge { display: inline-block; background: #e5e7eb; color: #374151; padding: 0.35rem 0.75rem;
                     border-radius: 6px; font-size: 0.8rem; font-weight: 500; }
        /* Chat: spacing only; do not override display/flex/overflow/position so avatars stay visible */
        [data-testid="stChatMessage"] { margin-bottom: 0.75rem; }
        /* Recruiter dashboard cards */
        .card { background: #fff; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                padding: 1.35rem; margin-bottom: 1.25rem; }
        .card pre { background: #f8f9fa; padding: 1rem; border-radius: 6px; overflow: auto; font-size: 0.9rem; }
        .card h3 { margin-top: 0 !important; }
        /* Sidebar */
        [data-testid="stSidebar"] { background: #fff; }
        [data-testid="stSidebar"] .block-container { padding: 1rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

def render_app_header(subtitle: str = "AI-Powered Technical Screening System") -> None:
    """Render main app title (centered), subtitle, and subtle divider."""
    st.markdown(
        f'<div class="header-area">'
        f'<h1>🤖 TalentScout Hiring Assistant</h1>'
        f'<p class="header-subtitle">{html.escape(subtitle)}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.divider()


def render_mode_badge(mode: str) -> None:
    """Render a small badge at top-right showing current mode (Candidate Mode / Recruiter Mode)."""
    col1, col2 = st.columns([5, 1])
    with col2:
        st.markdown(f'<span class="mode-badge">{html.escape(mode)}</span>', unsafe_allow_html=True)


def render_section(title: str, level: int = 2) -> None:
    """Render a section header and divider. level 2 = ##, level 3 = ###."""
    prefix = "#" * level
    st.markdown(f"{prefix} {title}")
    st.divider()


def render_card(title: str, content: str) -> None:
    """Render a styled card with title and preformatted content (content is escaped for HTML)."""
    escaped = html.escape(content)
    st.markdown(
        f"<div class='card'><h3>{html.escape(title)}</h3><pre>{escaped}</pre></div>",
        unsafe_allow_html=True,
    )
