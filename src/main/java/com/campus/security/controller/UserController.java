package com.campus.security.controller;

import com.campus.security.model.User;
import com.campus.security.model.UserSession;
import com.campus.security.service.UserService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    // Register a new student/staff user
    @PostMapping("/register")
    public ResponseEntity<?> register(
            @RequestParam String studentStaffNumber,
            @RequestParam String firstName,
            @RequestParam String lastName,
            @RequestParam String email,
            @RequestParam(required = false) String phoneNumber,
            @RequestParam String password,
            @RequestParam String roleName,
            @RequestParam Integer campusId) {

        try {

            User user = userService.registerUser(
                    studentStaffNumber,
                    firstName,
                    lastName,
                    email,
                    phoneNumber,
                    password,
                    roleName,
                    campusId
            );

            return ResponseEntity.ok(user);

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }

    // Login
    @PostMapping("/login")
    public ResponseEntity<?> login(
            @RequestParam String email,
            @RequestParam String password,
            @RequestParam(required = false) String deviceId,
            @RequestParam(required = false) String ipAddress) {

        try {

            UserSession session =
                    userService.login(
                            email,
                            password,
                            deviceId,
                            ipAddress
                    );

            return ResponseEntity.ok(session);

        } catch (RuntimeException e) {

            return ResponseEntity
                    .status(401)
                    .body(e.getMessage());
        }
    }

    // Logout
    @PostMapping("/logout")
    public ResponseEntity<?> logout(
            @RequestHeader("Authorization")
            String sessionToken) {

        try {

            // Remove "Bearer " if it exists
            sessionToken =
                    sessionToken.replace("Bearer ", "");

            userService.logout(sessionToken);

            return ResponseEntity.ok(
                    "Logout successful.");

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }

    // Get currently logged-in user
    @GetMapping("/me")
    public ResponseEntity<?> getCurrentUser(
            @RequestHeader("Authorization")
            String sessionToken) {

        try {

            sessionToken =
                    sessionToken.replace("Bearer ", "");

            User user =
                    userService.getUserFromSession(
                            sessionToken);

            return ResponseEntity.ok(user);

        } catch (RuntimeException e) {

            return ResponseEntity
                    .status(401)
                    .body(e.getMessage());
        }
    }
}