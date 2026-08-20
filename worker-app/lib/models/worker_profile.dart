class GigPlatform {
  final String id;
  final String name;
  final String logo; // Icon or asset key
  final double monthlyEarnings;
  final double rating;
  final int tripsCompleted;
  final bool isConnected;
  final String workType; // e.g. "Food Delivery", "Rideshare", "Logistics"

  GigPlatform({
    required this.id,
    required this.name,
    required this.logo,
    required this.monthlyEarnings,
    required this.rating,
    required this.tripsCompleted,
    required this.isConnected,
    required this.workType,
  });

  GigPlatform copyWith({bool? isConnected, double? monthlyEarnings}) {
    return GigPlatform(
      id: id,
      name: name,
      logo: logo,
      monthlyEarnings: monthlyEarnings ?? this.monthlyEarnings,
      rating: rating,
      tripsCompleted: tripsCompleted,
      isConnected: isConnected ?? this.isConnected,
      workType: workType,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'monthlyEarnings': monthlyEarnings,
    'rating': rating,
    'tripsCompleted': tripsCompleted,
    'isConnected': isConnected,
    'workType': workType,
  };
}

class WorkerProfile {
  final String id;
  final String name;
  final String email;
  final String phone;
  final String city;
  final String panNumber;
  final String upiId;
  final int totalMonthsExperience;
  final double avgDailyHours;
  final List<GigPlatform> platforms;
  final bool isOnboarded;

  WorkerProfile({
    required this.id,
    required this.name,
    required this.email,
    required this.phone,
    required this.city,
    required this.panNumber,
    required this.upiId,
    required this.totalMonthsExperience,
    required this.avgDailyHours,
    required this.platforms,
    required this.isOnboarded,
  });

  double get totalMonthlyEarnings {
    return platforms
        .where((p) => p.isConnected)
        .fold(0.0, (sum, p) => sum + p.monthlyEarnings);
  }

  int get totalConnectedPlatforms {
    return platforms.where((p) => p.isConnected).length;
  }

  double get averageRating {
    final connected = platforms.where((p) => p.isConnected).toList();
    if (connected.isEmpty) return 0.0;
    return connected.fold(0.0, (sum, p) => sum + p.rating) / connected.length;
  }

  WorkerProfile copyWith({
    String? name,
    String? email,
    String? phone,
    String? city,
    String? panNumber,
    String? upiId,
    int? totalMonthsExperience,
    double? avgDailyHours,
    List<GigPlatform>? platforms,
    bool? isOnboarded,
  }) {
    return WorkerProfile(
      id: id,
      name: name ?? this.name,
      email: email ?? this.email,
      phone: phone ?? this.phone,
      city: city ?? this.city,
      panNumber: panNumber ?? this.panNumber,
      upiId: upiId ?? this.upiId,
      totalMonthsExperience: totalMonthsExperience ?? this.totalMonthsExperience,
      avgDailyHours: avgDailyHours ?? this.avgDailyHours,
      platforms: platforms ?? this.platforms,
      isOnboarded: isOnboarded ?? this.isOnboarded,
    );
  }
}
