package com.campus.security.controller;

import com.campus.security.dto.LoginResponse;
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

    @PostMapping("/register")
    public ResponseEntity<?> register(
            @RequestParam String studentStaffNumber,
            @RequestParam String firstName,
            @RequestParam String lastName,
            @RequestParam(required = false) String phoneNumber,
            @RequestParam String password,
            @RequestParam String roleName,
            @RequestParam Integer campusId) {

        try {

            User user = userService.registerUser(
                    studentStaffNumber,
                    password,
                    firstName,
                    lastName,
                    phoneNumber,
                    roleName,
                    campusId
            );

            return ResponseEntity.ok(user);

        } catch (RuntimeException e) {

            return ResponseEntity
                    .badRequest()
                    .body(e.getMessage());
        }
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(
            @RequestParam String email,
            @RequestParam String password,
            @RequestParam(required = false) String deviceId,
            @RequestParam(required = false) String ipAddress) {

        try {

            UserSession session = userService.login(
                    email,
                    password,
                    deviceId,
                    ipAddress
            );

            LoginResponse response = new LoginResponse(
                    session.getSessionId(),
                    session.getSessionToken(),
                    session.getUser(),
                    session.getExpiryTime()
            );

            return ResponseEntity.ok(response);

        } catch (RuntimeException e) {
            return ResponseEntity.status(401).body(e.getMessage());
        }
    }

    @PostMapping("/logout")
    public ResponseEntity<?> logout(
            @RequestHeader("Authorization") String authorization) {

        try {

            if (!authorization.startsWith("Bearer ")) {
                throw new RuntimeException(
                        "Authorization token is required."
                );
            }

            userService.logout(
                    authorization.substring(7)
            );

            return ResponseEntity.ok("Logout successful.");

        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @GetMapping("/me")
    public ResponseEntity<?> getCurrentUser(
            @RequestHeader("Authorization") String authorization) {

        try {

            if (!authorization.startsWith("Bearer ")) {
                throw new RuntimeException(
                        "Authorization token is required."
                );
            }

            User user = userService.getUserFromSession(
                    authorization.substring(7)
            );

            return ResponseEntity.ok(user);

        } catch (RuntimeException e) {
            return ResponseEntity.status(401).body(e.getMessage());
        }
    }
}