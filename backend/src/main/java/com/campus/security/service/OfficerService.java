package com.campus.security.service;

import com.campus.security.model.Campus;
import com.campus.security.model.OfficerLocation;
import com.campus.security.model.SecurityOfficer;
import com.campus.security.model.AlertAssignment;
import com.campus.security.model.User;
import com.campus.security.repository.AlertAssignmentRepository;
import com.campus.security.repository.CampusRepository;
import com.campus.security.repository.OfficerLocationRepository;
import com.campus.security.repository.SecurityOfficerRepository;

import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class OfficerService {

    private final SecurityOfficerRepository officerRepository;
    private final OfficerLocationRepository locationRepository;
    private final CampusRepository campusRepository;
    private final AlertAssignmentRepository assignmentRepository;

    public OfficerService(
            SecurityOfficerRepository officerRepository,
            OfficerLocationRepository locationRepository,
            CampusRepository campusRepository,
            AlertAssignmentRepository assignmentRepository) {

        this.officerRepository = officerRepository;
        this.locationRepository = locationRepository;
        this.campusRepository = campusRepository;
        this.assignmentRepository = assignmentRepository;
    }

    public SecurityOfficer getOfficerForUser(User user) {
        return officerRepository
                .findByEmployeeNumber(user.getStudentStaffNumber())
                .orElseThrow(() -> new RuntimeException(
                        "No security officer profile is linked to this account."));
    }

    public List<AlertAssignment> getAssignments(User user) {
        return assignmentRepository.findByOfficerOrderByAssignedAtDesc(
                getOfficerForUser(user));
    }

    public AlertAssignment updateMyAssignment(
            User user,
            Integer assignmentId,
            AlertAssignment.AssignmentStatus status) {
        SecurityOfficer officer = getOfficerForUser(user);
        AlertAssignment assignment = assignmentRepository
                .findByAssignmentIdAndOfficer(assignmentId, officer)
                .orElseThrow(() -> new RuntimeException(
                        "Assigned emergency alert not found."));

        assignment.setAssignmentStatus(status);
        if (status == AlertAssignment.AssignmentStatus.COMPLETED) {
            assignment.setCompletedAt(LocalDateTime.now());
        }
        return assignmentRepository.save(assignment);
    }

    // Add a new security officer
    public SecurityOfficer addOfficer(
            String firstName,
            String lastName,
            String employeeNumber,
            String email,
            String phoneNumber,
            Integer campusId) {

        if (firstName == null || firstName.isBlank()
                || lastName == null || lastName.isBlank()
                || employeeNumber == null || employeeNumber.isBlank()
                || email == null || email.isBlank()) {
            throw new RuntimeException(
                    "First name, last name, employee number and email are required.");
        }

        // Check whether employee number already exists
        if (officerRepository
                .findByEmployeeNumber(employeeNumber)
                .isPresent()) {

            throw new RuntimeException(
                    "Employee number already exists.");
        }


        // Find campus
        Campus campus = campusRepository
                .findById(campusId)
                .orElseThrow(() ->
                        new RuntimeException(
                                "Campus not found."));

        SecurityOfficer officer =
                new SecurityOfficer();

        officer.setFirstName(firstName);
        officer.setLastName(lastName);
        officer.setEmployeeNumber(employeeNumber);
        officer.setPhoneNumber(phoneNumber);
        officer.setCampus(campus);

        // New officers start off duty
        officer.setAvailabilityStatus(
                SecurityOfficer.AvailabilityStatus.OFF_DUTY);

        return officerRepository.save(officer);
    }

    // Verify that an officer exists
    public SecurityOfficer verifyOfficer(
            String employeeNumber) {

        return officerRepository
                .findByEmployeeNumber(employeeNumber)
                .orElseThrow(() ->
                        new RuntimeException(
                                "Security officer not found."));
    }

    // Change officer availability
    public SecurityOfficer updateAvailability(
            Integer officerId,
            SecurityOfficer.AvailabilityStatus status) {

        SecurityOfficer officer =
                officerRepository.findById(officerId)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Security officer not found."));

        officer.setAvailabilityStatus(status);

        return officerRepository.save(officer);
    }

    // Capture the officer's current location
    public OfficerLocation updateOfficerLocation(
            Integer officerId,
            Double latitude,
            Double longitude) {

        if (latitude == null || longitude == null
                || latitude < -90 || latitude > 90
                || longitude < -180 || longitude > 180) {
            throw new RuntimeException(
                    "Valid GPS latitude and longitude are required.");
        }

        SecurityOfficer officer =
                officerRepository.findById(officerId)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Security officer not found."));

        OfficerLocation location =
                new OfficerLocation();

        location.setOfficer(officer);
        location.setLatitude(latitude);
        location.setLongitude(longitude);
        location.setCapturedAt(LocalDateTime.now());

        return locationRepository.save(location);
    }

    // Get the officer's latest location
    public OfficerLocation getLatestLocation(
            Integer officerId) {

        SecurityOfficer officer =
                officerRepository.findById(officerId)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Security officer not found."));

        return locationRepository
                .findTopByOfficerOrderByCapturedAtDesc(officer)
                .orElseThrow(() ->
                        new RuntimeException(
                                "Officer location not available."));
    }

    // Find all available officers
    public List<SecurityOfficer> getAvailableOfficers() {

        return officerRepository
                .findByAvailabilityStatus(
                        SecurityOfficer.AvailabilityStatus.AVAILABLE);
    }
}
