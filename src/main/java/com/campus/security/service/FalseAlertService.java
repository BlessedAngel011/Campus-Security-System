package com.campus.security.service;

import com.campus.security.model.Administrator;
import com.campus.security.model.EmergencyAlert;
import com.campus.security.model.FalseAlert;
import com.campus.security.model.Notification;
import com.campus.security.model.User;

import com.campus.security.repository.FalseAlertRepository;
import com.campus.security.repository.NotificationRepository;
import com.campus.security.repository.UserRepository;

import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class FalseAlertService {

    private final FalseAlertRepository falseAlertRepository;
    private final UserRepository userRepository;
    private final NotificationRepository notificationRepository;

    public FalseAlertService(
            FalseAlertRepository falseAlertRepository,
            UserRepository userRepository,
            NotificationRepository notificationRepository) {

        this.falseAlertRepository =
                falseAlertRepository;

        this.userRepository =
                userRepository;

        this.notificationRepository =
                notificationRepository;
    }

    // Mark an emergency alert as false
    public FalseAlert confirmFalseAlert(
            EmergencyAlert emergency,
            User user,
            Administrator admin,
            String reason) {

        FalseAlert falseAlert =
                new FalseAlert();

        falseAlert.setEmergencyAlert(emergency);
        falseAlert.setUser(user);
        falseAlert.setReviewedByAdmin(admin);
        falseAlert.setReason(reason);

        falseAlert.setFalseAlertStatus(
                FalseAlert.FalseAlertStatus.CONFIRMED_FALSE);

        falseAlert.setCreatedAt(
                LocalDateTime.now());

        falseAlert.setReviewedAt(
                LocalDateTime.now());

        falseAlert =
                falseAlertRepository.save(falseAlert);

        // Increase user's false alert count
        int currentCount =
                user.getFalseAlertCount() == null
                        ? 0
                        : user.getFalseAlertCount();

        currentCount++;

        user.setFalseAlertCount(currentCount);

        // Disable emergency button after 3 false alerts
        if (currentCount >= 3) {

            user.setEmergencyButtonEnabled(false);

            sendDisabledNotification(user);
        }

        userRepository.save(user);

        // Mark emergency as false
        emergency.setAlertStatus(
                EmergencyAlert.AlertStatus.FALSE_ALERT);

        return falseAlert;
    }

    // Send notification to user
    private void sendDisabledNotification(
            User user) {

        Notification notification =
                new Notification();

        notification.setUser(user);

        notification.setNotificationType(
                "EMERGENCY_BUTTON_DISABLED");

        notification.setMessage(
                "Your emergency button has been disabled "
                        + "because you submitted false alerts 3 times.");

        notification.setRead(false);

        notification.setCreatedAt(
                LocalDateTime.now());

        notificationRepository.save(notification);
    }

    // Mark an alert as NOT false
    public FalseAlert markNotFalse(
            EmergencyAlert emergency,
            User user,
            Administrator admin) {

        FalseAlert record =
                new FalseAlert();

        record.setEmergencyAlert(emergency);
        record.setUser(user);
        record.setReviewedByAdmin(admin);

        record.setFalseAlertStatus(
                FalseAlert.FalseAlertStatus.NOT_FALSE);

        record.setCreatedAt(
                LocalDateTime.now());

        record.setReviewedAt(
                LocalDateTime.now());

        return falseAlertRepository.save(record);
    }
}