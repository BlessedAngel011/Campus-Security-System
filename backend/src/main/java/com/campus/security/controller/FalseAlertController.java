package com.campus.security.controller;

import com.campus.security.model.Administrator;
import com.campus.security.model.EmergencyAlert;
import com.campus.security.model.FalseAlert;
import com.campus.security.repository.AdministratorRepository;
import com.campus.security.repository.EmergencyAlertRepository;
import com.campus.security.service.FalseAlertService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/false-alerts")
public class FalseAlertController {

    private final FalseAlertService falseAlertService;
    private final EmergencyAlertRepository emergencyRepository;
    private final AdministratorRepository adminRepository;

    public FalseAlertController(
            FalseAlertService falseAlertService,
            EmergencyAlertRepository emergencyRepository,
            AdministratorRepository adminRepository) {

        this.falseAlertService = falseAlertService;
        this.emergencyRepository = emergencyRepository;
        this.adminRepository = adminRepository;
    }

    /**
     * The userId is no longer accepted from Postman.
     * The reporting user is obtained directly from the emergency alert,
     * preventing an administrator from assigning a false alert to
     * a different user by changing userId.
     *
     * adminId remains because the current database has no user_id
     * relationship in the administrators table.
     */
    @PostMapping("/confirm")
    public ResponseEntity<?> confirmFalseAlert(
            @RequestParam Integer emergencyId,
            @RequestParam Integer adminId,
            @RequestParam String reason) {

        try {
            EmergencyAlert emergency =
                    emergencyRepository.findById(emergencyId)
                            .orElseThrow(() ->
                                    new RuntimeException(
                                            "Emergency alert not found."));

            Administrator admin =
                    adminRepository.findById(adminId)
                            .orElseThrow(() ->
                                    new RuntimeException(
                                            "Administrator not found."));

            FalseAlert falseAlert =
                    falseAlertService.confirmFalseAlert(
                            emergency,
                            admin,
                            reason);

            return ResponseEntity.ok(falseAlert);

        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PostMapping("/not-false")
    public ResponseEntity<?> markNotFalse(
            @RequestParam Integer emergencyId,
            @RequestParam Integer adminId) {

        try {
            EmergencyAlert emergency =
                    emergencyRepository.findById(emergencyId)
                            .orElseThrow(() ->
                                    new RuntimeException(
                                            "Emergency alert not found."));

            Administrator admin =
                    adminRepository.findById(adminId)
                            .orElseThrow(() ->
                                    new RuntimeException(
                                            "Administrator not found."));

            return ResponseEntity.ok(
                    falseAlertService.markNotFalse(
                            emergency, admin));

        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }
}
