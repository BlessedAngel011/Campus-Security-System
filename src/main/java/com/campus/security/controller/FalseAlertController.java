package com.campus.security.controller;

import com.campus.security.model.Administrator;
import com.campus.security.model.EmergencyAlert;
import com.campus.security.model.FalseAlert;
import com.campus.security.model.User;

import com.campus.security.repository.AdministratorRepository;
import com.campus.security.repository.EmergencyAlertRepository;
import com.campus.security.repository.UserRepository;

import com.campus.security.service.FalseAlertService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/false-alerts")
public class FalseAlertController {

    private final FalseAlertService falseAlertService;
    private final EmergencyAlertRepository emergencyRepository;
    private final UserRepository userRepository;
    private final AdministratorRepository adminRepository;

    public FalseAlertController(
            FalseAlertService falseAlertService,
            EmergencyAlertRepository emergencyRepository,
            UserRepository userRepository,
            AdministratorRepository adminRepository) {

        this.falseAlertService = falseAlertService;
        this.emergencyRepository = emergencyRepository;
        this.userRepository = userRepository;
        this.adminRepository = adminRepository;
    }

    // Confirm an emergency alert as false
    @PostMapping("/confirm")
    public ResponseEntity<?> confirmFalseAlert(
            @RequestParam Integer emergencyId,
            @RequestParam Integer userId,
            @RequestParam Integer adminId,
            @RequestParam String reason) {

        try {

            EmergencyAlert emergency =
                    emergencyRepository.findById(
                                    emergencyId)
                            .orElseThrow(() ->
                                    new RuntimeException(
                                            "Emergency alert not found."));

            User user =
                    userRepository.findById(userId)
                            .orElseThrow(() ->
                                    new RuntimeException(
                                            "User not found."));

            Administrator admin =
                    adminRepository.findById(adminId)
                            .orElseThrow(() ->
                                    new RuntimeException(
                                            "Administrator not found."));

            FalseAlert falseAlert =
                    falseAlertService.confirmFalseAlert(
                            emergency,
                            user,
                            admin,
                            reason
                    );

            return ResponseEntity.ok(falseAlert);

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }

    // Mark an emergency as not false
    @PostMapping("/not-false")
    public ResponseEntity<?> markNotFalse(
            @RequestParam Integer emergencyId,
            @RequestParam Integer userId,
            @RequestParam Integer adminId) {

        try {

            EmergencyAlert emergency =
                    emergencyRepository.findById(
                                    emergencyId)
                            .orElseThrow(() ->
                                    new RuntimeException(
                                            "Emergency alert not found."));

            User user =
                    userRepository.findById(userId)
                            .orElseThrow(() ->
                                    new RuntimeException(
                                            "User not found."));

            Administrator admin =
                    adminRepository.findById(adminId)
                            .orElseThrow(() ->
                                    new RuntimeException(
                                            "Administrator not found."));

            return ResponseEntity.ok(
                    falseAlertService.markNotFalse(
                            emergency,
                            user,
                            admin));

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }
}