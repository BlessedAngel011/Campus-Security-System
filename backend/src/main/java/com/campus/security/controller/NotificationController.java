package com.campus.security.controller;

import com.campus.security.model.Notification;
import com.campus.security.model.User;
import com.campus.security.service.NotificationService;
import com.campus.security.service.UserService;
import com.campus.security.service.OfficerService;
import com.campus.security.model.SecurityOfficer;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/notifications")
public class NotificationController {

    private final NotificationService notificationService;
    private final UserService userService;
    private final OfficerService officerService;

    public NotificationController(
            NotificationService notificationService,
            UserService userService,
            OfficerService officerService) {
        this.notificationService = notificationService;
        this.userService = userService;
        this.officerService = officerService;
    }

    @GetMapping("/officer/my-notifications")
    public ResponseEntity<?> getOfficerNotifications(
            @RequestHeader("Authorization") String authorization) {
        try {
            User user = getAuthenticatedUser(authorization);
            SecurityOfficer officer = officerService.getOfficerForUser(user);
            return ResponseEntity.ok(
                    notificationService.getOfficerNotifications(officer));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PutMapping("/officer/{notificationId}/read")
    public ResponseEntity<?> markOfficerNotificationRead(
            @RequestHeader("Authorization") String authorization,
            @PathVariable Integer notificationId) {
        try {
            User user = getAuthenticatedUser(authorization);
            SecurityOfficer officer = officerService.getOfficerForUser(user);
            return ResponseEntity.ok(
                    notificationService.markOfficerNotificationAsRead(
                            notificationId, officer));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    private User getAuthenticatedUser(String authorization) {
        if (authorization == null || !authorization.startsWith("Bearer ")) {
            throw new RuntimeException("Authorization token is required.");
        }
        return userService.getUserFromSession(
                authorization.substring(7));
    }

    @GetMapping("/my-notifications")
    public ResponseEntity<?> getMyNotifications(
            @RequestHeader("Authorization") String authorization) {
        try {
            User user = getAuthenticatedUser(authorization);
            return ResponseEntity.ok(
                    notificationService.getUserNotifications(user));
        } catch (RuntimeException e) {
            return ResponseEntity.status(401).body(e.getMessage());
        }
    }

    @PutMapping("/{notificationId}/read")
    public ResponseEntity<?> markAsRead(
            @RequestHeader("Authorization") String authorization,
            @PathVariable Integer notificationId) {
        try {
            User user = getAuthenticatedUser(authorization);
            Notification notification =
                    notificationService.markAsRead(notificationId, user);
            return ResponseEntity.ok(notification);
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @GetMapping("/unread")
    public ResponseEntity<?> getUnread(
            @RequestHeader("Authorization") String authorization) {
        try {
            User user = getAuthenticatedUser(authorization);
            return ResponseEntity.ok(
                    notificationService.getUnreadNotifications(user));
        } catch (RuntimeException e) {
            return ResponseEntity.status(401).body(e.getMessage());
        }
    }
}
