package com.campus.security.controller;

import com.campus.security.model.OfficerLocation;
import com.campus.security.model.SecurityOfficer;
import com.campus.security.service.OfficerService;
import com.campus.security.service.UserService;
import com.campus.security.model.User;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import com.campus.security.model.AlertAssignment;

@RestController
@RequestMapping("/api/officers")
public class OfficerController {

    private final OfficerService officerService;
    private final UserService userService;

    public OfficerController(OfficerService officerService,
                             UserService userService) {
        this.officerService = officerService;
        this.userService = userService;
    }

    private User authenticatedUser(String authorization) {
        if (authorization == null || !authorization.startsWith("Bearer ")) {
            throw new RuntimeException("Authorization token is required.");
        }
        return userService.getUserFromSession(authorization.substring(7));
    }

    @GetMapping("/me")
    public ResponseEntity<?> getMyOfficerProfile(
            @RequestHeader("Authorization") String authorization) {
        try {
            return ResponseEntity.ok(officerService.getOfficerForUser(
                    authenticatedUser(authorization)));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @GetMapping("/me/assignments")
    public ResponseEntity<?> getMyAssignments(
            @RequestHeader("Authorization") String authorization) {
        try {
            return ResponseEntity.ok(officerService.getAssignments(
                    authenticatedUser(authorization)));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PutMapping("/me/availability")
    public ResponseEntity<?> updateMyAvailability(
            @RequestHeader("Authorization") String authorization,
            @RequestParam SecurityOfficer.AvailabilityStatus status) {
        try {
            SecurityOfficer officer = officerService.getOfficerForUser(
                    authenticatedUser(authorization));
            return ResponseEntity.ok(officerService.updateAvailability(
                    officer.getOfficerId(), status));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PostMapping("/me/location")
    public ResponseEntity<?> updateMyLocation(
            @RequestHeader("Authorization") String authorization,
            @RequestParam Double latitude,
            @RequestParam Double longitude) {
        try {
            SecurityOfficer officer = officerService.getOfficerForUser(
                    authenticatedUser(authorization));
            return ResponseEntity.ok(officerService.updateOfficerLocation(
                    officer.getOfficerId(), latitude, longitude));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PutMapping("/me/assignments/{assignmentId}/status")
    public ResponseEntity<?> updateMyAssignment(
            @RequestHeader("Authorization") String authorization,
            @PathVariable Integer assignmentId,
            @RequestParam AlertAssignment.AssignmentStatus status) {
        try {
            return ResponseEntity.ok(officerService.updateMyAssignment(
                    authenticatedUser(authorization), assignmentId, status));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    // Add security officer
    @PostMapping
    public ResponseEntity<?> addOfficer(
            @RequestParam String firstName,
            @RequestParam String lastName,
            @RequestParam String employeeNumber,
            @RequestParam String email,
            @RequestParam(required = false) String phoneNumber,
            @RequestParam Integer campusId) {

        try {

            SecurityOfficer officer =
                    officerService.addOfficer(
                            firstName,
                            lastName,
                            employeeNumber,
                            email,
                            phoneNumber,
                            campusId
                    );

            return ResponseEntity.ok(officer);

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }

    // Verify officer employee number
    @GetMapping("/verify/{employeeNumber}")
    public ResponseEntity<?> verifyOfficer(
            @PathVariable String employeeNumber) {

        try {

            return ResponseEntity.ok(
                    officerService.verifyOfficer(
                            employeeNumber));

        } catch (RuntimeException e) {

            return ResponseEntity.notFound().build();
        }
    }

    // Change officer availability
    @PutMapping("/{officerId}/availability")
    public ResponseEntity<?> updateAvailability(
            @PathVariable Integer officerId,
            @RequestParam
            SecurityOfficer.AvailabilityStatus status) {

        try {

            return ResponseEntity.ok(
                    officerService.updateAvailability(
                            officerId,
                            status));

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }

    // Save current GPS location
    @PostMapping("/{officerId}/location")
    public ResponseEntity<?> updateLocation(
            @PathVariable Integer officerId,
            @RequestParam Double latitude,
            @RequestParam Double longitude) {

        try {

            OfficerLocation location =
                    officerService.updateOfficerLocation(
                            officerId,
                            latitude,
                            longitude
                    );

            return ResponseEntity.ok(location);

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }

    // Get latest officer location
    @GetMapping("/{officerId}/location")
    public ResponseEntity<?> getLocation(
            @PathVariable Integer officerId) {

        try {

            return ResponseEntity.ok(
                    officerService.getLatestLocation(
                            officerId));

        } catch (RuntimeException e) {

            return ResponseEntity.notFound().build();
        }
    }

    // Get all available officers
    @GetMapping("/available")
    public ResponseEntity<List<SecurityOfficer>>
    getAvailableOfficers() {

        return ResponseEntity.ok(
                officerService.getAvailableOfficers());
    }
}
