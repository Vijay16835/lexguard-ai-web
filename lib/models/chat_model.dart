enum MessageSender { user, ai }

class ChatMessage {
  final String id;
  final String content;
  final MessageSender sender;
  final DateTime timestamp;
  final bool isLoading;

  ChatMessage({
    required this.id,
    required this.content,
    required this.sender,
    required this.timestamp,
    this.isLoading = false,
  });

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'content': content,
      'sender': sender.index,
      'timestamp': timestamp.toIso8601String(),
    };
  }

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: json['id'],
      content: json['content'],
      sender: MessageSender.values[json['sender']],
      timestamp: DateTime.parse(json['timestamp']),
    );
  }



  static List<String> get suggestedPrompts => [
    'Summarize this agreement',
    'What are the payment terms?',
    'Is there any penalty clause?',
    'What is the contract duration?',
    'Who are the parties involved?',
    'What are the termination conditions?',
    'Are there any arbitration clauses?',
    'What obligations does each party have?',
  ];
}
