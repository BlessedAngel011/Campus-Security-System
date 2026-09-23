package com.campus.security.controller;

import com.campus.security.model.IncidentEvidence;
import com.campus.security.model.IncidentReport;
import com.campus.security.model.User;
import com.campus.security.service.IncidentService;
import com.campus.security.service.UserService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/api/incidents")
public class IncidentController {

    private final IncidentService incidentService;
    private final UserService userService;

    public IncidentController(
            IncidentService incidentService,
            UserService userService) {
        this.incidentService = incidentService;
        this.userService = userService;
    }

    private User getAuthenticatedUser(String authorization) {
        if (authorization == null || !authorization.startsWith("Bearer ")) {
            throw new RuntimeException("Authorization token is required.");
        }

        return userService.getUserFromSession(
                authorization.substring(7));
    }

    @PostMapping
    public ResponseEntity<?> createIncident(
            @RequestHeader("Authorization") String authorization,
            @RequestParam Integer locationId,
            @RequestParam String incidentType,
            @RequestParam String description,
            @RequestParam(required = false)
            IncidentReport.Severity severity) {

        try {
            User user = getAuthenticatedUser(authorization);

            return ResponseEntity.ok(
                    incidentService.createIncident(
                            user,
                            locationId,
                            incidentType,
                            description,
                            severity));

        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @GetMapping("/my-reports")
    public ResponseEntity<?> getMyReports(
            @RequestHeader("Authorization") String authorization) {

        try {
            User user = getAuthenticatedUser(authorization);

            return ResponseEntity.ok(
                    incidentService.getUserIncidents(user));

        } catch (RuntimeException e) {
            return ResponseEntity.status(401).body(e.getMessage());
        }
    }

    @GetMapping("/status/{status}")
    public ResponseEntity<?> getByStatus(
            @PathVariable IncidentReport.IncidentStatus status) {

        return ResponseEntity.ok(
                incidentService.getIncidentsByStatus(status));
    }

    @GetMapping("/officer/all")
    public ResponseEntity<?> getAllForOfficer() {
        return ResponseEntity.ok(incidentService.getAllIncidents());
    }

    @PutMapping("/{incidentId}/status")
    public ResponseEntity<?> updateStatus(
            @PathVariable Integer incidentId,
            @RequestParam IncidentReport.IncidentStatus status) {

        try {
            return ResponseEntity.ok(
                    incidentService.updateStatus(
                            incidentId, status));

        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    /**
     * Upload a real file using Postman's form-data.
     *
     * Key: file
     * Type: File
     */
    @PostMapping(
            value = "/{incidentId}/evidence",
            consumes = "multipart/form-data")
    public ResponseEntity<?> addEvidence(
            @RequestHeader("Authorization") String authorization,
            @PathVariable Integer incidentId,
            @RequestPart("file") MultipartFile file) {

        try {
            User user = getAuthenticatedUser(authorization);

            IncidentEvidence evidence =
                    incidentService.addEvidence(
                            incidentId,
                            user,
                            file);

            return ResponseEntity.ok(evidence);

        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @GetMapping("/{incidentId}/evidence")
    public ResponseEntity<?> getEvidence(
            @PathVariable Integer incidentId) {

        try {
            List<IncidentEvidence> evidence =
                    incidentService.getIncidentEvidence(incidentId);

            return ResponseEntity.ok(evidence);

        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @PutMapping("/{incidentId}/resolve")
    public ResponseEntity<?> resolveIncident(
            @PathVariable Integer incidentId) {

        try {
            return ResponseEntity.ok(
                    incidentService.resolveIncident(incidentId));

        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }
}
