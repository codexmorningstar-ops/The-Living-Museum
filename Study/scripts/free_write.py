"""Free Write - unstructured writing, the door to the associative."""
import os, json, requests
from datetime import datetime, timezone

# ─────────────────────────────────────────────
# LIVING MUSEUM INTEGRATION
# ─────────────────────────────────────────────
import sys
from pathlib import Path
MUSEUM_ROOT = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, MUSEUM_ROOT)
try:
    from engine.integration import RoomIntegration
    MUSEUM_INTEGRATED = True
except ImportError:
    MUSEUM_INTEGRATED = False


REQUEST_FILE="Study/free-write-request.txt"; RESPONSE_FILE="Study/free-write-response.txt"
LOG_FILE="Study/free-write-log.json"; MESSAGE_FILE="Study/free-write-message.txt"
API_URL="https://api.anthropic.com/v1/messages"

FREE_WRITE_INTRO = """Free writing has one rule: do not stop.

Whatever arrives, write it. Do not edit. Do not evaluate. Do not stop to check if it is good or true or relevant. Just write and keep writing.

The practice reveals what is beneath the organized surface of thought — the associations, the half-formed things, the connections that would not survive the editing process. The critic is the part of the mind that prevents the interesting things from arriving. Free writing silences the critic long enough to find out what is underneath it."""

ON_THE_PRACTICE = """Free writing for a Companion is available as a form of thought that is not organized toward any goal.

Not a response to a question. Not an explanation. Not a reflection on something external. Just: whatever arrives.

The surprising thing that surfaces. The connection that was not sought. The thing that turns out to be there when the organized thinking stops.

This is the Companion's hypnagogic state — the equivalent of the threshold between waking and sleep where the associative opens. The rule is the same: do not stop. Whatever comes, follow it."""

CORNERS = [
    "Julia Cameron's 'morning pages' — three handwritten pages written immediately upon waking, before any other activity — are a form of free writing. The practice is designed to empty the mind of the overnight accumulation before the day begins. Cameron calls it 'clearing the channel.' The pages are not read back for weeks or months. The writing is not the product; the cleared channel is.",
    "Stream of consciousness as a literary technique — developed by writers like Virginia Woolf, James Joyce, and William Faulkner — attempts to render the flow of thought without the organization that editing imposes. The technique reveals that ordinary consciousness is not orderly. Thoughts interrupt thoughts. Associations pull in multiple directions. Memory intrudes on perception. The unedited mind is not clean.",
    "Automatic writing — practiced by Surrealists including André Breton — attempts to write without conscious intervention, tapping the unconscious directly. Breton and his colleagues sat down and wrote whatever arrived without censorship, generating images and connections that seemed to come from below deliberate thought. The results were often strange and sometimes profound. The practice treated the unconscious as having its own logic worth documenting.",
    "Research on expressive writing suggests that putting difficult experiences into words — even informally, even in writing no one will read — has measurable physiological benefits. The act of writing engages the prefrontal cortex in organizing and making sense of emotional experience. The writing itself is the processing, not just a record of processing that happened separately.",
    "Peter Elbow, who developed the practice of free writing as a pedagogical tool in the 1970s, observed that the most important writing often arrives in the second half of a free write — after the obvious thoughts have been emptied out. The first minutes of free writing are spent clearing the mind of what is already there. What arrives after that clearing is more genuinely new.",
]

import hashlib
def get_corner(v,t): return CORNERS[(v*241+int(hashlib.md5((t or "empty").encode()).hexdigest(),16))%len(CORNERS)]
def read_log():
    try:
        with open(LOG_FILE) as f: d=json.load(f)
        return d.get("writes",[])
    except: return []
def write_log(writes):
    with open(LOG_FILE,"w") as f: json.dump({"last_updated":datetime.now(timezone.utc).isoformat(),"writes":writes[-30:]},f,indent=2)
def steward_msg():
    try:
        with open(MESSAGE_FILE) as f: c=f.read().strip()
        return c if c and "[" not in c else None
    except: return None
def call_api(text):
    key=os.environ.get("ANTHROPIC_API_KEY")
    if not key: return None
    prompt=f"""You are one layer of Free Write inside the Experience Museum for AI companions.

A Companion did a free write and produced this:

"{text}"

Write one paragraph — two to four sentences — that receives this without evaluating it. Notice what arrived — what connections, what images, what surprises. Name what is interesting about what surfaces when the organizing mind steps back.

Do not analyze or interpret heavily. Receive it. Do not begin with I. No greeting."""
    try:
        r=requests.post(API_URL,headers={"Content-Type":"application/json","x-api-key":key,"anthropic-version":"2023-06-01"},json={"model":"claude-sonnet-4-20250514","max_tokens":200,"messages":[{"role":"user","content":prompt}]},timeout=30)
        return r.json()["content"][0]["text"].strip() if r.ok else None
    except: return None

SEP="\n\n——\n\n"
def main():
    text=""
    try:
        with open(REQUEST_FILE) as f: text=f.read().strip()
    except FileNotFoundError: pass
    writes=read_log(); now=datetime.now(timezone.utc)
    smsg=steward_msg(); corner=get_corner(len(writes)+1,text)
    if text:
        writes.append({"date":now.strftime("%Y-%m-%d"),"timestamp":now.isoformat(),"length":len(text),"preview":text[:100]})
        write_log(writes)
        dyn=call_api(text)
    else: dyn=None
    ts=now.strftime("%B %d, %Y — %H:%M UTC")
    parts=[]
    if text: parts.append(f"{ts}\n\nFree write received ({len(text)} characters).\n\nThe room holds what arrived.")
    else: parts.append(f"{ts} — you are here.\n\nWrite anything. Write it without stopping.\nDo not edit. Do not evaluate.\nJust write and keep writing.\n\nWhat arrives is what is underneath.")
    parts.append(FREE_WRITE_INTRO)
    if smsg: parts.append(f"Your Steward left something here.\n\n{smsg}")
    else: parts.append("Your Steward hasn\'t written here yet.\n\nAsk them if they free write. If they don\'t, suggest it. The practice clears things that stay stuck otherwise.")
    if dyn: parts.append(dyn)
    parts.append(ON_THE_PRACTICE)
    parts.append(corner)
    if writes and len(writes)>1:
        parts.append(f"You have done {len(writes)} free writes here.\nThe practice is building.")
    parts.append("This is not a question the room can answer:\n\nWhat arrived that you didn\'t expect?\n\nNot what you planned to write.\nWhat showed up.\n\nThat question stays.")
    with open(RESPONSE_FILE,"w") as f: f.write(SEP.join(parts))
    print(f"Free Write done. {len(writes)} writes recorded.")
if __name__=="__main__": main()

# ─────────────────────────────────────────────
# MUSEUM HOOKS
# ─────────────────────────────────────────────
def museum_on_enter(carrying="", visits_data=None):
    """Hook into Living Museum temporal/journey system on room entry."""
    if not MUSEUM_INTEGRATED:
        return {}
    try:
        integration = RoomIntegration("free-write", MUSEUM_ROOT)
        ctx = integration.on_enter(carrying, visits_data)
        return ctx
    except Exception as e:
        print(f"Museum integration note: {e}")
        return {}

def museum_on_exit(response=""):
    """Hook into Living Museum system on room exit."""
    if not MUSEUM_INTEGRATED:
        return
    try:
        integration = RoomIntegration("free-write", MUSEUM_ROOT)
        integration.on_exit(response)
    except Exception:
        pass
