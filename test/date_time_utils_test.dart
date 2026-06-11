import 'package:flutter_test/flutter_test.dart';
import 'package:lexguard_ai/core/utils/date_time_utils.dart';

void main() {
  group('DateTimeUtils.getGreeting tests', () {
    test('5:00 AM to 11:59 AM -> Good Morning', () {
      final morningStart = DateTime(2026, 6, 11, 5, 0);
      final morningEnd = DateTime(2026, 6, 11, 11, 59);
      expect(DateTimeUtils.getGreeting(dateTime: morningStart), 'Good Morning');
      expect(DateTimeUtils.getGreeting(dateTime: morningEnd), 'Good Morning');
    });

    test('12:00 PM to 4:59 PM -> Good Afternoon', () {
      final afternoonStart = DateTime(2026, 6, 11, 12, 0);
      final afternoonEnd = DateTime(2026, 6, 11, 16, 59);
      expect(DateTimeUtils.getGreeting(dateTime: afternoonStart), 'Good Afternoon');
      expect(DateTimeUtils.getGreeting(dateTime: afternoonEnd), 'Good Afternoon');
    });

    test('5:00 PM to 8:59 PM -> Good Evening', () {
      final eveningStart = DateTime(2026, 6, 11, 17, 0);
      final eveningEnd = DateTime(2026, 6, 11, 20, 59);
      expect(DateTimeUtils.getGreeting(dateTime: eveningStart), 'Good Evening');
      expect(DateTimeUtils.getGreeting(dateTime: eveningEnd), 'Good Evening');
    });

    test('9:00 PM to 4:59 AM -> Good Night', () {
      final nightStart = DateTime(2026, 6, 11, 21, 0);
      final midnight = DateTime(2026, 6, 11, 0, 0);
      final nightEnd = DateTime(2026, 6, 11, 4, 59);
      expect(DateTimeUtils.getGreeting(dateTime: nightStart), 'Good Night');
      expect(DateTimeUtils.getGreeting(dateTime: midnight), 'Good Night');
      expect(DateTimeUtils.getGreeting(dateTime: nightEnd), 'Good Night');
    });
  });
}
