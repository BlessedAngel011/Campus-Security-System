package com.campus.security.controller;

import com.campus.security.model.Administrator;
import com.campus.security.model.VerificationCode;
import com.campus.security.service.AdminService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/admin")
public class AdminController {

    private final AdminService adminService;

    public AdminController(AdminService adminService) {
        this.adminService = adminService;
    }

    // Check administrator employee number and university email
    @PostMapping("/verify-details")
    public ResponseEntity<?> verifyDetails(
            @RequestParam String employeeNumber,
            @RequestParam String universityEmail) {

        try {

            Administrator admin =
                    adminService.verifyAdminDetails(
                            employeeNumber,
                            universityEmail
                    );

            return ResponseEntity.ok(admin);

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }

    // Generate verification code
    @PostMapping("/send-code")
    public ResponseEntity<?> sendCode(
            @RequestParam String employeeNumber,
            @RequestParam String universityEmail) {

        try {

            VerificationCode code =
                    adminService.generateVerificationCode(
                            employeeNumber,
                            universityEmail
                    );

            return ResponseEntity.ok(code);

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }

    // Confirm verification code
    @PostMapping("/confirm-code")
    public ResponseEntity<?> confirmCode(
            @RequestParam String employeeNumber,
            @RequestParam String code) {

        try {

            Administrator admin =
                    adminService.confirmVerificationCode(
                            employeeNumber,
                            code
                    );

            return ResponseEntity.ok(admin);

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }
}