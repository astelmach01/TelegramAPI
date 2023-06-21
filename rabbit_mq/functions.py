from website.api.messages import post_message
from website.api.conversations import get_conversations, get_conversation_by_id
from website.api.sender import get_sender_by_id


functions = {
    "post_message": post_message,
    "getConversations": get_conversations,
    "getConversationById": get_conversation_by_id,
    "getSenderById": get_sender_by_id,
}
