/// Helper functions related to date and time formatting and utilities.
class DateTimeUtils {
  /// Returns a dynamic greeting based on the hour of the day:
  /// - 5:00 AM to 11:59 AM -> Good Morning
  /// - 12:00 PM to 4:59 PM -> Good Afternoon
  /// - 5:00 PM to 8:59 PM -> Good Evening
  /// - 9:00 PM to 4:59 AM -> Good Night
  static String getGreeting({DateTime? dateTime}) {
    final dt = dateTime ?? DateTime.now();
    final hour = dt.hour;
    if (hour >= 5 && hour < 12) {
      return 'Good Morning';
    } else if (hour >= 12 && hour < 17) {
      return 'Good Afternoon';
    } else if (hour >= 17 && hour < 21) {
      return 'Good Evening';
    } else {
      return 'Good Night';
    }
  }
}
