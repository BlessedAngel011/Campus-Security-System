package com.campus.security.service;

import com.campus.security.model.AlertAssignment;
import com.campus.security.model.EmergencyAlert;
import com.campus.security.model.Notification;
import com.campus.security.model.SecurityOfficer;
import com.campus.security.model.User;
import com.campus.security.repository.AlertAssignmentRepository;
import com.campus.security.repository.EmergencyAlertRepository;
import com.campus.security.repository.NotificationRepository;
import com.campus.security.repository.OfficerLocationRepository;
import com.campus.security.repository.SecurityOfficerRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class EmergencyService {

    private final EmergencyAlertRepository emergencyRepository;
    private final AlertAssignmentRepository assignmentRepository;
    private final SecurityOfficerRepository officerRepository;
    private final OfficerLocationRepository officerLocationRepository;
    private final NotificationRepository notificationRepository;

    public EmergencyService(
            EmergencyAlertRepository emergencyRepository,
            AlertAssignmentRepository assignmentRepository,
            SecurityOfficerRepository officerRepository,
            OfficerLocationRepository officerLocationRepository,
            NotificationRepository notificationRepository) {

        this.emergencyRepository = emergencyRepository;
        this.assignmentRepository = assignmentRepository;
        this.officerRepository = officerRepository;
        this.officerLocationRepository = officerLocationRepository;
        this.notificationRepository = notificationRepository;
    }

    public EmergencyAlert createEmergencyAlert(
            User user,
            Double latitude,
            Double longitude,
            String emergencyType,
            String description) {

        validateCoordinates(latitude, longitude);

        if (!Boolean.TRUE.equals(
                user.getEmergencyButtonEnabled())) {
            throw new RuntimeException(
                    "Emergency button is disabled because you submitted false alerts 3 times.");
        }

        EmergencyAlert emergency = new EmergencyAlert();
        emergency.setUser(user);
        emergency.setLatitude(latitude);
        emergency.setLongitude(longitude);
        emergency.setEmergencyType(
                emergencyType == null || emergencyType.isBlank()
                        ? "GENERAL_EMERGENCY"
                        : emergencyType.trim());
        emergency.setDescription(description);
        emergency.setAlertStatus(
                EmergencyAlert.AlertStatus.SENT);
        emergency.setCreatedAt(LocalDateTime.now());

        emergency = emergencyRepository.save(emergency);

        SecurityOfficer nearestOfficer =
                findNearestAvailableOfficer(
                        latitude, longitude);

        if (nearestOfficer != null) {
            assignEmergency(
                    emergency,
                    nearestOfficer,
                    latitude,
                    longitude);
        } else {
            Notification notification = new Notification();
            notification.setUser(user);
            notification.setNotificationType(
                    "NO_OFFICER_AVAILABLE");
            notification.setMessage(
                    "Your emergency alert was received, "
                            + "but no available security officer "
                            + "with a current location was found.");
            notification.setRead(false);
            notification.setCreatedAt(LocalDateTime.now());
            notificationRepository.save(notification);
        }

        return emergency;
    }

    public SecurityOfficer findNearestAvailableOfficer(
            Double userLatitude,
            Double userLongitude) {

        List<SecurityOfficer> officers =
                officerRepository.findByAvailabilityStatus(
                        SecurityOfficer.AvailabilityStatus.AVAILABLE);

        SecurityOfficer nearestOfficer = null;
        double shortestDistance = Double.MAX_VALUE;

        for (SecurityOfficer officer : officers) {

            var location =
                    officerLocationRepository
                            .findTopByOfficerOrderByCapturedAtDesc(
                                    officer);

            if (location.isEmpty()) {
                continue;
            }

            double distance = calculateDistance(
                    userLatitude,
                    userLongitude,
                    location.get().getLatitude(),
                    location.get().getLongitude());

            if (distance < shortestDistance) {
                shortestDistance = distance;
                nearestOfficer = officer;
            }
        }

        return nearestOfficer;
    }

    private void assignEmergency(
            EmergencyAlert emergency,
            SecurityOfficer officer,
            Double userLatitude,
            Double userLongitude) {

        var latestLocation =
                officerLocationRepository
                        .findTopByOfficerOrderByCapturedAtDesc(
                                officer);

        if (latestLocation.isEmpty()) {
            return;
        }

        double distance = calculateDistance(
                userLatitude,
                userLongitude,
                latestLocation.get().getLatitude(),
                latestLocation.get().getLongitude());

        AlertAssignment assignment =
                new AlertAssignment();

        assignment.setEmergencyAlert(emergency);
        assignment.setOfficer(officer);
        assignment.setDistanceKm(distance);
        assignment.setAssignmentStatus(
                AlertAssignment.AssignmentStatus.ASSIGNED);
        assignment.setAssignedAt(LocalDateTime.now());

        assignmentRepository.save(assignment);

        Notification notification = new Notification();
        notification.setOfficer(officer);
        notification.setNotificationType("EMERGENCY_ALERT");
        notification.setMessage(
                "Emergency alert received. "
                        + "You are the nearest available security officer.");
        notification.setRead(false);
        notification.setCreatedAt(LocalDateTime.now());

        notificationRepository.save(notification);
    }

    private double calculateDistance(
            double latitude1,
            double longitude1,
            double latitude2,
            double longitude2) {

        final double EARTH_RADIUS = 6371.0;

        double latDistance =
                Math.toRadians(latitude2 - latitude1);
        double lonDistance =
                Math.toRadians(longitude2 - longitude1);

        double a =
                Math.sin(latDistance / 2)
                        * Math.sin(latDistance / 2)
                        + Math.cos(Math.toRadians(latitude1))
                        * Math.cos(Math.toRadians(latitude2))
                        * Math.sin(lonDistance / 2)
                        * Math.sin(lonDistance / 2);

        double c =
                2 * Math.atan2(
                        Math.sqrt(a),
                        Math.sqrt(1 - a));

        return EARTH_RADIUS * c;
    }

    public EmergencyAlert getEmergency(
            Integer emergencyId,
            User currentUser) {

        EmergencyAlert emergency = getEmergency(emergencyId);

        if (canViewEmergency(emergency, currentUser)) {
            return emergency;
        }

        throw new RuntimeException(
                "You are not allowed to view this emergency alert.");
    }

    public EmergencyAlert getEmergency(Integer emergencyId) {
        return emergencyRepository.findById(emergencyId)
                .orElseThrow(() ->
                        new RuntimeException(
                                "Emergency alert not found."));
    }

    public EmergencyAlert updateEmergencyStatus(
            Integer emergencyId,
            EmergencyAlert.AlertStatus status) {

        if (status == null) {
            throw new RuntimeException(
                    "Emergency status is required.");
        }

        EmergencyAlert emergency = getEmergency(emergencyId);
        emergency.setAlertStatus(status);

        if (status ==
                EmergencyAlert.AlertStatus.RESOLVED) {
            emergency.setResolvedAt(LocalDateTime.now());
        }

        return emergencyRepository.save(emergency);
    }

    private boolean canViewEmergency(
            EmergencyAlert emergency,
            User currentUser) {

        String role = currentUser.getRole()
                .getRoleName()
                .replace(" ", "_")
                .toUpperCase();

        return emergency.getUser().getUserId()
                .equals(currentUser.getUserId())
                || role.equals("ADMIN")
                || role.equals("SECURITY_OFFICER");
    }

    private void validateCoordinates(
            Double latitude,
            Double longitude) {

        if (latitude == null
                || longitude == null
                || latitude < -90
                || latitude > 90
                || longitude < -180
                || longitude > 180) {

            throw new RuntimeException(
                    "Valid GPS latitude and longitude are required.");
        }
    }
}
