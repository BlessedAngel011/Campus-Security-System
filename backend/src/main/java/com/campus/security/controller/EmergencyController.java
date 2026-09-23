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

    private User getAuthenticatedUser(String authorization) {
        if (authorization == null
                || !authorization.startsWith("Bearer ")) {
            throw new RuntimeException(
                    "Authorization token is required.");
        }

        return userService.getUserFromSession(
                authorization.substring(7));
    }

    @PostMapping("/alert")
    public ResponseEntity<?> createEmergency(
            @RequestHeader("Authorization") String authorization,
            @RequestParam Double latitude,
            @RequestParam Double longitude,
            @RequestParam(required = false) String emergencyType,
            @RequestParam(required = false) String description) {

        try {
            User user = getAuthenticatedUser(authorization);

            return ResponseEntity.ok(
                    emergencyService.createEmergencyAlert(
                            user,
                            latitude,
                            longitude,
                            emergencyType,
                            description));

        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @GetMapping("/{emergencyId}")
    public ResponseEntity<?> getEmergency(
            @RequestHeader("Authorization") String authorization,
            @PathVariable Integer emergencyId) {

        try {
            User user = getAuthenticatedUser(authorization);

            return ResponseEntity.ok(
                    emergencyService.getEmergency(
                            emergencyId, user));

        } catch (RuntimeException e) {
            return ResponseEntity.status(403).body(e.getMessage());
        }
    }

    @PutMapping("/{emergencyId}/status")
    public ResponseEntity<?> updateStatus(
            @PathVariable Integer emergencyId,
            @RequestParam EmergencyAlert.AlertStatus status) {

        try {
            return ResponseEntity.ok(
                    emergencyService.updateEmergencyStatus(
                            emergencyId, status));

        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }
}
