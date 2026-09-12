package com.campus.security.controller;

import com.campus.security.model.EmergencyAlert;
import com.campus.security.model.User;
import com.campus.security.service.EmergencyService;
import com.campus.security.service.UserService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/emergency")
public class EmergencyController {

    private final EmergencyService emergencyService;
    private final UserService userService;

    public EmergencyController(
            EmergencyService emergencyService,
            UserService userService) {

        this.emergencyService = emergencyService;
        this.userService = userService;
    }

    // Rapid Response button
    @PostMapping("/alert")
    public ResponseEntity<?> createEmergency(
            @RequestHeader("Authorization")
            String sessionToken,
            @RequestParam Double latitude,
            @RequestParam Double longitude,
            @RequestParam(required = false)
            String emergencyType,
            @RequestParam(required = false)
            String description) {

        try {

            sessionToken =
                    sessionToken.replace("Bearer ", "");

            // Identify user from existing session
            User user =
                    userService.getUserFromSession(
                            sessionToken);

            EmergencyAlert alert =
                    emergencyService.createEmergencyAlert(
                            user,
                            latitude,
                            longitude,
                            emergencyType,
                            description
                    );

            return ResponseEntity.ok(alert);

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }

    // Get emergency alert
    @GetMapping("/{emergencyId}")
    public ResponseEntity<?> getEmergency(
            @PathVariable Integer emergencyId) {

        try {

            return ResponseEntity.ok(
                    emergencyService.getEmergency(
                            emergencyId));

        } catch (RuntimeException e) {

            return ResponseEntity.notFound().build();
        }
    }

    // Update emergency status
    @PutMapping("/{emergencyId}/status")
    public ResponseEntity<?> updateStatus(
            @PathVariable Integer emergencyId,
            @RequestParam
            EmergencyAlert.AlertStatus status) {

        try {

            return ResponseEntity.ok(
                    emergencyService
                            .updateEmergencyStatus(
                                    emergencyId,
                                    status));

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }
}