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
import com.campus.security.repository.FalseAlertRepository;
import com.campus.security.repository.UserRepository;
import com.campus.security.model.FalseAlert;
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
    private final FalseAlertRepository falseAlertRepository;
    private final UserRepository userRepository;

    public EmergencyService(
            EmergencyAlertRepository emergencyRepository,
            AlertAssignmentRepository assignmentRepository,
            SecurityOfficerRepository officerRepository,
            OfficerLocationRepository officerLocationRepository,
            NotificationRepository notificationRepository,
            FalseAlertRepository falseAlertRepository,
            UserRepository userRepository) {

        this.emergencyRepository = emergencyRepository;
        this.assignmentRepository = assignmentRepository;
        this.officerRepository = officerRepository;
        this.officerLocationRepository = officerLocationRepository;
        this.notificationRepository = notificationRepository;
        this.falseAlertRepository = falseAlertRepository;
        this.userRepository = userRepository;
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
                    "Emergency SOS access is suspended because more than 3 emergency alerts were confirmed false. Contact Campus Security/Admin.");
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
                        latitude, longitude, user);

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
            Double userLongitude,
            User emergencyUser) {

        List<SecurityOfficer> officers =
                officerRepository.findByAvailabilityStatus(
                        SecurityOfficer.AvailabilityStatus.AVAILABLE);

        SecurityOfficer nearestOfficer = null;
        double shortestDistance = Double.MAX_VALUE;

        for (SecurityOfficer officer : officers) {

            // Only dispatch officers assigned to the same campus as the user.
            if (emergencyUser.getCampus() == null
                    || officer.getCampus() == null
                    || !emergencyUser.getCampus().getCampusId().equals(
                            officer.getCampus().getCampusId())) {
                continue;
            }

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
        String reporterName = ((emergency.getUser().getFirstName() == null ? "" : emergency.getUser().getFirstName())
                + " " + (emergency.getUser().getLastName() == null ? "" : emergency.getUser().getLastName())).trim();
        notification.setMessage(
                "Emergency alert received. You are the nearest available security officer. "
                        + "Reporter: " + (reporterName.isBlank() ? "Unknown" : reporterName)
                        + ", number: " + (emergency.getUser().getStudentStaffNumber() == null ? "Not supplied" : emergency.getUser().getStudentStaffNumber())
                        + ". Open Assigned Emergencies to accept the SOS and view the latest location.");
        notification.setRead(false);
        notification.setCreatedAt(LocalDateTime.now());

        notificationRepository.save(notification);
    }

    public EmergencyAlert resolveEmergencyWithReview(
            Integer emergencyId, User currentUser, boolean falseAlert, String review) {
        if (review == null || review.trim().length() < 10)
            throw new RuntimeException("Write an officer review of at least 10 characters.");

        EmergencyAlert emergency = getEmergency(emergencyId);
        SecurityOfficer officer = officerRepository.findByEmployeeNumber(currentUser.getStudentStaffNumber())
                .orElseThrow(() -> new RuntimeException("No security officer profile is linked to this account."));
        assignmentRepository.findByEmergencyAlertAndOfficer(emergency, officer)
                .orElseThrow(() -> new RuntimeException("This emergency is not assigned to you."));

        emergency.setOfficerReview(review.trim());
        emergency.setConfirmedFalse(falseAlert);
        emergency.setResolvedAt(LocalDateTime.now());

        User reporter = emergency.getUser();
        if (falseAlert) {
            if (!falseAlertRepository.existsByEmergencyAlertAndFalseAlertStatus(
                    emergency, FalseAlert.FalseAlertStatus.CONFIRMED_FALSE)) {
                FalseAlert record = new FalseAlert();
                record.setEmergencyAlert(emergency);
                record.setUser(reporter);
                record.setReason(review.trim());
                record.setFalseAlertStatus(FalseAlert.FalseAlertStatus.CONFIRMED_FALSE);
                record.setCreatedAt(LocalDateTime.now());
                falseAlertRepository.save(record);

                int count = reporter.getFalseAlertCount() == null ? 0 : reporter.getFalseAlertCount();
                count++;
                reporter.setFalseAlertCount(count);
                if (count > 3) {
                    reporter.setEmergencyButtonEnabled(false);
                    notifyUser(reporter, "EMERGENCY_BUTTON_SUSPENDED",
                            "Your SOS button has been suspended after more than 3 confirmed false emergency alerts. Contact Campus Security/Admin.");
                } else {
                    notifyUser(reporter, "FALSE_EMERGENCY_WARNING",
                            "An emergency alert was confirmed false. You now have " + count +
                                    " false alert(s). More than 3 will suspend SOS access.");
                }
                userRepository.save(reporter);
            }
            emergency.setAlertStatus(EmergencyAlert.AlertStatus.FALSE_ALERT);
        } else {
            emergency.setAlertStatus(EmergencyAlert.AlertStatus.RESOLVED);
            notifyUser(reporter, "EMERGENCY_RESOLVED",
                    "Your emergency alert has been resolved by Campus Security.");
        }
        return emergencyRepository.save(emergency);
    }

    private void notifyUser(User user, String type, String message) {
        Notification n = new Notification();
        n.setUser(user); n.setNotificationType(type); n.setMessage(message);
        n.setRead(false); n.setCreatedAt(LocalDateTime.now());
        notificationRepository.save(n);
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

    public List<EmergencyAlert> getOfficerActiveEmergencies(User currentUser) {
        SecurityOfficer officer = officerRepository.findByEmployeeNumber(currentUser.getStudentStaffNumber())
                .orElseThrow(() -> new RuntimeException("No security officer profile is linked to this account."));
        return assignmentRepository.findByOfficerOrderByAssignedAtDesc(officer).stream()
                .map(AlertAssignment::getEmergencyAlert)
                .filter(e -> e.getAlertStatus() != EmergencyAlert.AlertStatus.RESOLVED
                        && e.getAlertStatus() != EmergencyAlert.AlertStatus.CANCELLED
                        && e.getAlertStatus() != EmergencyAlert.AlertStatus.FALSE_ALERT)
                .toList();
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

    public EmergencyAlert updateEmergencyLocation(
            Integer emergencyId, User currentUser, Double latitude, Double longitude) {
        validateCoordinates(latitude, longitude);
        EmergencyAlert emergency = getEmergency(emergencyId);
        if (!emergency.getUser().getUserId().equals(currentUser.getUserId())) {
            throw new RuntimeException("Only the user who sent this SOS can update its location.");
        }
        if (emergency.getAlertStatus() == EmergencyAlert.AlertStatus.RESOLVED
                || emergency.getAlertStatus() == EmergencyAlert.AlertStatus.FALSE_ALERT
                || emergency.getAlertStatus() == EmergencyAlert.AlertStatus.CANCELLED) {
            throw new RuntimeException("This emergency is already closed.");
        }
        emergency.setLatitude(latitude);
        emergency.setLongitude(longitude);
        return emergencyRepository.save(emergency);
    }

    public EmergencyAlert updateEmergencyStatus(
            Integer emergencyId,
            EmergencyAlert.AlertStatus status,
            User currentUser) {
        if (status == null) throw new RuntimeException("Emergency status is required.");
        if (status == EmergencyAlert.AlertStatus.RESOLVED || status == EmergencyAlert.AlertStatus.FALSE_ALERT)
            throw new RuntimeException("Complete the officer review before closing an emergency.");

        EmergencyAlert emergency = getEmergency(emergencyId);
        SecurityOfficer officer = officerRepository.findByEmployeeNumber(currentUser.getStudentStaffNumber())
                .orElseThrow(() -> new RuntimeException("No security officer profile is linked to this account."));
        assignmentRepository.findByEmergencyAlertAndOfficer(emergency, officer)
                .orElseThrow(() -> new RuntimeException("This emergency is not assigned to you."));
        emergency.setAlertStatus(status);
        EmergencyAlert saved = emergencyRepository.save(emergency);
        notifyUser(emergency.getUser(), "EMERGENCY_STATUS_CHANGED",
                "Your emergency alert is now " + status.name().replace('_', ' ').toLowerCase() + ".");
        return saved;
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
