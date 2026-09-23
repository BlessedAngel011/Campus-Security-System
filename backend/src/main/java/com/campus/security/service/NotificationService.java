package com.campus.security.service;

import com.campus.security.model.Administrator;
import com.campus.security.model.EmergencyAlert;
import com.campus.security.model.Notification;
import com.campus.security.model.SecurityOfficer;
import com.campus.security.model.User;

import com.campus.security.repository.NotificationRepository;

import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class NotificationService {

    private final NotificationRepository notificationRepository;

    public NotificationService(
            NotificationRepository notificationRepository) {

        this.notificationRepository =
                notificationRepository;
    }

    // Send notification to a normal user
    public Notification notifyUser(
            User user,
            String type,
            String message) {

        Notification notification =
                new Notification();

        notification.setUser(user);
        notification.setNotificationType(type);
        notification.setMessage(message);
        notification.setRead(false);
        notification.setCreatedAt(
                LocalDateTime.now());

        return notificationRepository.save(
                notification);
    }

    // Send notification to security officer
    public Notification notifyOfficer(
            SecurityOfficer officer,
            String type,
            String message,
            EmergencyAlert emergency) {

        Notification notification =
                new Notification();

        notification.setOfficer(officer);
        notification.setNotificationType(type);
        notification.setMessage(message);
        notification.setRead(false);
        notification.setCreatedAt(
                LocalDateTime.now());

        return notificationRepository.save(
                notification);
    }

    // Send notification to administrator
    public Notification notifyAdmin(
            Administrator admin,
            String type,
            String message) {

        Notification notification =
                new Notification();

        notification.setAdministrator(admin);
        notification.setNotificationType(type);
        notification.setMessage(message);
        notification.setRead(false);
        notification.setCreatedAt(
                LocalDateTime.now());

        return notificationRepository.save(
                notification);
    }

    // Get user's notifications
    public List<Notification> getUserNotifications(
            User user) {

        return notificationRepository
                .findByUserOrderByCreatedAtDesc(user);
    }

    // Mark a notification as read only if it belongs to the current user.
    public Notification markAsRead(
            Integer notificationId,
            User currentUser) {

        Notification notification =
                notificationRepository
                        .findById(notificationId)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Notification not found."));

        if (notification.getUser() == null
                || !notification.getUser().getUserId()
                .equals(currentUser.getUserId())) {

            throw new RuntimeException(
                    "You are not allowed to modify this notification.");
        }

        notification.setRead(true);

        return notificationRepository.save(
                notification);
    }

    // Get unread notifications belonging to the current user.
    public List<Notification> getUnreadNotifications(User user) {

        return notificationRepository
                .findByUserAndReadFalseOrderByCreatedAtDesc(user);
    }

    public List<Notification> getOfficerNotifications(
            SecurityOfficer officer) {
        return notificationRepository
                .findByOfficerOrderByCreatedAtDesc(officer);
    }

    public Notification markOfficerNotificationAsRead(
            Integer notificationId,
            SecurityOfficer officer) {
        Notification notification = notificationRepository
                .findById(notificationId)
                .orElseThrow(() -> new RuntimeException(
                        "Notification not found."));

        if (notification.getOfficer() == null
                || !notification.getOfficer().getOfficerId()
                .equals(officer.getOfficerId())) {
            throw new RuntimeException(
                    "You are not allowed to modify this notification.");
        }

        notification.setRead(true);
        return notificationRepository.save(notification);
    }
}
