package com.campus.security.controller;

import com.campus.security.model.Notification;
import com.campus.security.model.User;

import com.campus.security.service.NotificationService;
import com.campus.security.service.UserService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/notifications")
public class NotificationController {

    private final NotificationService notificationService;
    private final UserService userService;

    public NotificationController(
            NotificationService notificationService,
            UserService userService) {

        this.notificationService = notificationService;
        this.userService = userService;
    }

    // Get notifications for logged-in user
    @GetMapping("/my-notifications")
    public ResponseEntity<?> getMyNotifications(
            @RequestHeader("Authorization")
            String sessionToken) {

        try {

            sessionToken =
                    sessionToken.replace("Bearer ", "");

            User user =
                    userService.getUserFromSession(
                            sessionToken);

            return ResponseEntity.ok(
                    notificationService
                            .getUserNotifications(user));

        } catch (RuntimeException e) {

            return ResponseEntity.status(401)
                    .body(e.getMessage());
        }
    }

    // Mark notification as read
    @PutMapping("/{notificationId}/read")
    public ResponseEntity<?> markAsRead(
            @PathVariable Integer notificationId) {

        try {

            Notification notification =
                    notificationService.markAsRead(
                            notificationId);

            return ResponseEntity.ok(notification);

        } catch (RuntimeException e) {

            return ResponseEntity.badRequest()
                    .body(e.getMessage());
        }
    }

    // Get unread notifications
    @GetMapping("/unread")
    public ResponseEntity<?> getUnread() {

        return ResponseEntity.ok(
                notificationService
                        .getUnreadNotifications());
    }
}