"""Password rules for accounts people create themselves.

Following NIST SP 800-63B, length and a deny-list matter more than composition rules, so a password must be 10 to 128
characters, not a common password, not contain the product or demo-brand name, not contain the person's name or
email, and not be repetitive or digits-only. BrandGuard never stores passwords: Supabase Auth keeps a bcrypt hash, and
the offline demo store keeps a salted PBKDF2 hash.
"""
import re
from typing import Optional

MIN_LEN, MAX_LEN = 10, 128

# Checked after lower-casing, keeping only letters and digits, and dropping trailing digits ("Password123" -> "password")
COMMON_BASES = {
    "password", "passw0rd", "qwerty", "qwertyuiop", "asdfghjkl", "letmein", "welcome", "iloveyou", "admin",
    "administrator", "changeme", "monkey", "dragon", "football", "baseball", "master", "login", "abc", "secret",
    "trustno", "sunshine", "princess", "whatever", "freedom", "hello", "shadow", "superman", "batman", "india",
    "demo", "test", "testing",
}
# Anyone who has seen the site can guess these, so they are rejected anywhere in a password
PRODUCT_WORDS = ("brandguard", "glowleaf", "inkloom")


def _alnum(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def check_password(password: str, *, email: str = "", name: str = "") -> Optional[str]:
    """Why the password isn't acceptable, worded for the person signing up, or None if it's fine."""
    if len(password) < MIN_LEN:
        return f"Use at least {MIN_LEN} characters. A short phrase of unrelated words works well."
    if len(password) > MAX_LEN:
        return f"Use at most {MAX_LEN} characters."
    if len(set(password)) < 5:
        return "That password repeats too few characters. Try a longer, less predictable one."
    plain = _alnum(password)
    if not re.search(r"[a-z]", plain):
        return "Add letters: a password made only of digits and symbols is too easy to guess."
    if any(word in plain for word in PRODUCT_WORDS):
        return "Don't use the product or brand name in your password; it is easy to guess."
    base = re.sub(r"\d+$", "", plain)
    near_common = any(base.startswith(c) and len(base) - len(c) <= 2 for c in COMMON_BASES if len(c) >= 6)
    if base in COMMON_BASES or near_common:
        return "That password is too common. Choose something only you would think of."
    local_part = _alnum(email.split("@")[0])
    if len(local_part) >= 4 and local_part in plain:
        return "Your password should not contain your email address."
    if any(len(part) >= 4 and part in plain for part in map(_alnum, name.split())):
        return "Your password should not contain your name."
    return None
