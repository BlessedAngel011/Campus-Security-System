package com.campus.security.controller;

import com.campus.security.model.Administrator;
import com.campus.security.model.VerificationCode;
import com.campus.security.service.AdminService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import com.campus.security.model.User;

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

            return ResponseEntity.ok(Map.of(
                    "message", "Verification code created.",
                    "verificationCode", code.getVerificationCode(),
                    "expiresAt", code.getExpiresAt()));

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

            return ResponseEntity.ok(Map.of(
                    "token", adminService.createSessionToken(admin),
                    "administrator", admin));

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }

    @GetMapping("/dashboard")
    public ResponseEntity<?> dashboard() { return ResponseEntity.ok(adminService.getDashboardStats()); }

    @GetMapping("/users")
    public ResponseEntity<?> users() { return ResponseEntity.ok(adminService.getUsers()); }

    @PutMapping("/users/{userId}/status")
    public ResponseEntity<?> updateUserStatus(@PathVariable Integer userId,
            @RequestParam User.AccountStatus status) {
        try { return ResponseEntity.ok(adminService.updateUserStatus(userId, status)); }
        catch (RuntimeException e) { return ResponseEntity.badRequest().body(e.getMessage()); }
    }
    @GetMapping("/officers/workloads")
    public ResponseEntity<?> officerWorkloads() {

        return ResponseEntity.ok(
                adminService.getOfficerWorkloads()
        );
    }

    @GetMapping("/officers")
    public ResponseEntity<?> officers() { return ResponseEntity.ok(adminService.getOfficers()); }

    @PostMapping("/officers")
    public ResponseEntity<?> createOfficer(@RequestParam String firstName,
            @RequestParam String lastName, @RequestParam String employeeNumber,
            @RequestParam String password, @RequestParam(required=false) String phoneNumber,
            @RequestParam Integer campusId) {
        try { return ResponseEntity.ok(adminService.createOfficer(firstName, lastName,
                employeeNumber, password, phoneNumber, campusId)); }
        catch (RuntimeException e) { return ResponseEntity.badRequest().body(e.getMessage()); }
    }

    @GetMapping("/emergencies")
    public ResponseEntity<?> emergencies() { return ResponseEntity.ok(adminService.getEmergencies()); }

    @GetMapping("/incidents")
    public ResponseEntity<?> incidents() { return ResponseEntity.ok(adminService.getIncidents()); }

    @GetMapping("/campuses")
    public ResponseEntity<?> campuses() { return ResponseEntity.ok(adminService.getCampuses()); }
}
