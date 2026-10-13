"""Editable website content.

Every section has a built-in default (the launch copy). Admins override sections from the admin
panel; the overrides are stored as JSON in `site_settings`, one row per section. The public site
always receives defaults merged with overrides, so a missing or partial override never breaks a page.
"""
from __future__ import annotations

import copy
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings

# Icons the public site knows how to draw (lucide names, kebab-case).
ICONS = (
    "globe", "code", "server", "workflow", "compass", "presentation", "users", "monitor-play", "life-buoy",
    "lightbulb", "shield-check", "award", "accessibility", "trending-up", "check-circle", "graduation-cap",
    "rocket", "briefcase", "heart-handshake", "sparkles", "target", "eye", "book-open", "cpu", "cloud", "lock",
)
Icon = Literal[ICONS]  # type: ignore[valid-type]

TOPICS = ("Technology / Software Project", "Web Development", "IT Consulting", "Digital Transformation",
          "Corporate Training", "LMS / Learning Enquiry", "Partnership", "General Enquiry")
Topic = Literal[TOPICS]  # type: ignore[valid-type]


def _s(n: int, default: str = ""):
    return Field(default=default, max_length=n)


# ---------------------------------------------------------------- section schemas
class HomeIn(BaseModel):
    badge: str = _s(80)
    headline: str = _s(120)
    highlight: str = _s(80)
    lead: str = _s(400)
    learn_title: str = _s(120)
    learn_text: str = _s(600)
    services_title: str = _s(120)
    services_lead: str = _s(400)
    why_title: str = _s(120)
    why_text: str = _s(400)
    cta_title: str = _s(120)
    cta_text: str = _s(400)


class ServiceItem(BaseModel):
    icon: Icon = "globe"
    title: str = Field(min_length=2, max_length=80)
    summary: str = _s(200)          # short line used on the home page cards
    text: str = _s(600)             # longer description on the Services page
    topic: Topic = "General Enquiry"
    on_home: bool = True


class ServicesIn(BaseModel):
    hero_title: str = _s(120)
    hero_lead: str = _s(500)
    items: list[ServiceItem] = Field(default_factory=list, max_length=12)
    cta_title: str = _s(120)
    cta_text: str = _s(400)


class Card(BaseModel):
    icon: Icon = "sparkles"
    title: str = Field(min_length=2, max_length=60)
    text: str = _s(300)


class ReasonsIn(BaseModel):
    items: list[Card] = Field(default_factory=list, max_length=8)


class AboutIn(BaseModel):
    hero_title: str = _s(120)
    hero_lead: str = _s(600)
    intro: str = _s(600)
    vision: str = _s(600)
    mission: str = _s(600)
    values: list[Card] = Field(default_factory=list, max_length=8)
    what_we_do: str = _s(800)
    commitment: str = _s(800)


class ContactIn(BaseModel):
    email: str = _s(255)
    phone: str = _s(50)
    address: str = _s(300)
    hours: str = _s(120)
    hero_title: str = _s(120)
    hero_lead: str = _s(400)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip()
        if v and ("@" not in v or " " in v or len(v.split("@")[-1].split(".")) < 2):
            raise ValueError("Enter a valid email address or leave it empty")
        return v


def _url(v: str) -> str:
    v = (v or "").strip()
    if v and not v.startswith(("https://", "http://")):
        raise ValueError("Links must start with https://")
    return v


class SocialIn(BaseModel):
    facebook: str = _s(300)
    linkedin: str = _s(300)
    instagram: str = _s(300)
    x: str = _s(300)
    youtube: str = _s(300)

    @field_validator("facebook", "linkedin", "instagram", "x", "youtube")
    @classmethod
    def _links(cls, v: str) -> str:
        return _url(v)


class BannerIn(BaseModel):
    enabled: bool = False
    text: str = _s(200)
    link_label: str = _s(40)
    link_url: str = _s(300)
    tone: Literal["brand", "amber", "slate"] = "brand"

    @field_validator("link_url")
    @classmethod
    def _link(cls, v: str) -> str:
        v = (v or "").strip()
        if v and not (v.startswith("/") or v.startswith("https://")):
            raise ValueError("Use a site path like /courses or a full https:// link")
        if v.startswith("//"):
            raise ValueError("Use a site path like /courses or a full https:// link")
        return v


class LegalIn(BaseModel):
    privacy_html: Optional[str] = Field(default=None, max_length=60000)
    terms_html: Optional[str] = Field(default=None, max_length=60000)
    updated: str = _s(40)


SECTIONS: dict[str, type[BaseModel]] = {
    "home": HomeIn, "services": ServicesIn, "reasons": ReasonsIn, "about": AboutIn,
    "contact": ContactIn, "social": SocialIn, "banner": BannerIn, "legal": LegalIn,
}


# ---------------------------------------------------------------- defaults (launch copy)
def defaults() -> dict:
    return copy.deepcopy({
        "home": {
            "badge": "Technology. Learning. Innovation. Growth.",
            "headline": "Empowering People and Organizations",
            "highlight": "Through Technology",
            "lead": "Technology solutions and practical online learning that help businesses, institutions and individuals thrive.",
            "learn_title": "Build Skills. Advance Your Career. Keep Learning.",
            "learn_text": "Our Learning Management System gives learners access to structured courses and digital learning "
                          "resources designed to support professional development, digital skills, entrepreneurship, and lifelong learning.",
            "services_title": "Solutions that move your organization forward",
            "services_lead": "We provide technology solutions designed to help organizations improve productivity, efficiency, "
                             "digital operations, and service delivery.",
            "why_title": "Technology that creates possibilities",
            "why_text": "Infohive Technology Ltd. combines practical technology solutions and digital learning to solve real-world challenges.",
            "cta_title": "Ready to Learn, Build, or Transform?",
            "cta_text": "Whether you need a technology solution, digital transformation support, training, or access to practical "
                        "online courses, Infohive Technology Ltd. is ready to help.",
        },
        "services": {
            "hero_title": "Technology Solutions Designed Around Your Needs",
            "hero_lead": "At Infohive Technology Ltd., we help businesses, institutions, and individuals use technology more "
                         "effectively. Our services are designed to improve digital presence, operational efficiency, "
                         "productivity, and access to modern technology.",
            "items": [
                {"icon": "globe", "title": "Web Development", "on_home": False, "topic": "Web Development",
                 "summary": "Modern, responsive websites that communicate clearly.",
                 "text": "We design and develop modern, responsive websites that help businesses and organizations establish a strong digital presence and communicate effectively with their audiences."},
                {"icon": "code", "title": "Web & Software Development", "on_home": True, "topic": "Technology / Software Project",
                 "summary": "Modern websites and tailored software for your business and operations.",
                 "text": "We develop software and digital applications tailored to specific business, institutional, and operational needs."},
                {"icon": "server", "title": "IT Solutions & Consulting", "on_home": True, "topic": "IT Consulting",
                 "summary": "Practical guidance and systems that improve productivity and day-to-day operations.",
                 "text": "We provide practical technology solutions and guidance that help organizations improve their systems, processes, productivity, and day-to-day operations, and choose the right technology."},
                {"icon": "workflow", "title": "Digital Transformation", "on_home": True, "topic": "Digital Transformation",
                 "summary": "Adopt digital tools and processes that lift efficiency and customer experience.",
                 "text": "We help organizations adopt digital tools and processes that improve efficiency, customer experience, communication, and business performance."},
                {"icon": "presentation", "title": "Technology Training", "on_home": True, "topic": "Corporate Training",
                 "summary": "Hands-on training that builds relevant digital capabilities for people and teams.",
                 "text": "We provide practical technology training designed to help individuals, employees, and organizations develop relevant digital capabilities."},
                {"icon": "users", "title": "Corporate & Employee Training", "on_home": False, "topic": "Corporate Training",
                 "summary": "Staff development, onboarding and compliance training on our platform.",
                 "text": "Organizations can use our learning platform to deliver staff development, onboarding, compliance, skills development, and other training programs."},
                {"icon": "monitor-play", "title": "LMS & Digital Learning Solutions", "on_home": True, "topic": "LMS / Learning Enquiry",
                 "summary": "Deliver, manage and monitor online learning for your organization.",
                 "text": "We provide learning technology solutions that enable organizations and training providers to deliver, manage, and monitor online learning."},
                {"icon": "life-buoy", "title": "Digital Support & Maintenance", "on_home": True, "topic": "General Enquiry",
                 "summary": "Ongoing support that keeps your platforms reliable and effective.",
                 "text": "We provide ongoing technical support and maintenance to help keep digital platforms and technology solutions reliable and effective."},
            ],
            "cta_title": "Let's Build Something Better",
            "cta_text": "Tell us what you want to build, improve, automate, or learn. Our team can help you identify the right "
                        "technology or learning solution for your needs.",
        },
        "reasons": {"items": [
            {"icon": "check-circle", "title": "Practical Solutions", "text": "We focus on solutions that address real needs and create measurable value."},
            {"icon": "lightbulb", "title": "Innovation", "text": "We embrace technology and new ideas to deliver better solutions."},
            {"icon": "award", "title": "Quality", "text": "We are committed to excellence in our services and learning experiences."},
            {"icon": "accessibility", "title": "Accessibility", "text": "We believe technology and knowledge should be accessible to more people."},
            {"icon": "trending-up", "title": "Growth", "text": "We help individuals and organizations continuously learn, improve, and grow."},
        ]},
        "about": {
            "hero_title": "Technology With Purpose. Learning With Impact.",
            "hero_lead": "Infohive Technology Ltd. is a technology and digital learning company focused on delivering practical "
                         "technology solutions and creating opportunities for individuals and organizations to develop the "
                         "knowledge and skills needed in today's digital economy.",
            "intro": "We believe technology should do more than automate processes. It should create opportunities, improve "
                     "access to information, strengthen organizations, and empower people to achieve more.",
            "vision": "To become a leading technology and digital learning company that empowers individuals and organizations "
                      "across Africa and beyond to achieve more through technology, innovation, and knowledge.",
            "mission": "To deliver innovative technology solutions and accessible learning opportunities that enable people and "
                       "organizations to improve their capabilities, solve problems, and achieve sustainable growth.",
            "values": [
                {"icon": "lightbulb", "title": "Innovation", "text": "We seek better, smarter, and more effective ways to solve problems."},
                {"icon": "shield-check", "title": "Integrity", "text": "We build relationships based on trust, transparency, and accountability."},
                {"icon": "award", "title": "Excellence", "text": "We strive to deliver quality in every service and learning experience."},
                {"icon": "accessibility", "title": "Accessibility", "text": "We work toward making technology and knowledge easier to access."},
                {"icon": "trending-up", "title": "Growth", "text": "We believe continuous learning and improvement are essential to success."},
            ],
            "what_we_do": "Our work brings together technology services and digital learning. We support organizations with "
                          "technology solutions while providing individuals and teams with opportunities to learn new skills through our LMS.",
            "commitment": "We are committed to creating technology experiences that are useful, reliable, accessible, and focused "
                          "on real-world results. As technology continues to evolve, we aim to remain a trusted partner for "
                          "organizations and individuals navigating the digital future.",
        },
        # contact + social start from the deployment's environment variables
        "contact": {
            "email": settings.CONTACT_EMAIL or "", "phone": settings.CONTACT_PHONE or "",
            "address": settings.CONTACT_ADDRESS or "", "hours": settings.CONTACT_HOURS or "",
            "hero_title": "Let's Talk",
            "hero_lead": "Have a project, training need, partnership opportunity, or question about our services? We would be happy to hear from you.",
        },
        "social": {
            "facebook": settings.SOCIAL_FACEBOOK or "", "linkedin": settings.SOCIAL_LINKEDIN or "",
            "instagram": settings.SOCIAL_INSTAGRAM or "", "x": settings.SOCIAL_X or "", "youtube": "",
        },
        "banner": {"enabled": False, "text": "", "link_label": "", "link_url": "", "tone": "brand"},
        "legal": {"privacy_html": None, "terms_html": None, "updated": ""},
    })
