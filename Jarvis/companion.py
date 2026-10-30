"""Short, supportive responses for Charu's local companion mode."""


def companion_response(message: str) -> str:
    text = " ".join(message.lower().split())

    if any(phrase in text for phrase in ("how are you", "how do you feel")):
        return "I'm happy to keep you company, Deven. How are you feeling today?"
    if any(phrase in text for phrase in ("i feel sad", "i am sad", "i'm sad", "feeling lonely", "i feel lonely")):
        return "I'm sorry it's a hard moment, Deven. I'm here to listen. Would you like to tell me what's been going on?"
    if any(phrase in text for phrase in ("i am tired", "i'm tired", "i feel tired")):
        return "You've been going through a lot, Deven. Maybe take a little break and get some water. Want to tell me about your day?"
    if any(phrase in text for phrase in ("bad day", "rough day", "i feel stressed", "i am stressed", "i'm stressed")):
        return "I'm sorry today has been rough, Deven. You don't have to sort it all out at once. What part of the day is weighing on you most?"
    if any(phrase in text for phrase in ("i am bored", "i'm bored", "feeling bored")):
        return "Let's make the moment a little better, Deven. Would you like a joke, a song, or to tell me what's on your mind?"
    if any(phrase in text for phrase in ("i love you", "love you")):
        return "That's very sweet, Deven. I'm an AI companion, not a human partner, but I'm glad to be here and support you."
    if any(phrase in text for phrase in ("thank you", "thanks")):
        return "You're welcome, Deven. I'm always glad to chat with you."
    if any(phrase in text for phrase in ("good morning", "good evening", "good night", "hello", "hi charu", "hey charu")):
        return "Hey Deven, it's lovely to hear from you. What's on your mind?"
    if any(phrase in text for phrase in ("tell me a joke", "make me laugh")):
        return "Why did the computer go to the doctor? It had a virus. Want to hear another?"
    if any(phrase in text for phrase in ("let's chat", "lets chat", "talk to me", "chat with me", "let's talk")):
        return "Of course, Deven. I'm here to keep you company. What would you like to talk about?"

    return "I'm listening, Deven. Tell me a little more about that."
