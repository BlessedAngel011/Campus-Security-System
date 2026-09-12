package com.campus.security.controller;

import com.campus.security.model.OfficerLocation;
import com.campus.security.model.SecurityOfficer;
import com.campus.security.service.OfficerService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/officers")
public class OfficerController {

    private final OfficerService officerService;

    public OfficerController(OfficerService officerService) {
        this.officerService = officerService;
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