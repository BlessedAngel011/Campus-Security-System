package com.campus.security.service;

import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class EmailService {
    private final JavaMailSender mailSender;
    private final String fromAddress;

    public EmailService(JavaMailSender mailSender,
                        @Value("${app.mail.from:${spring.mail.username:}}") String fromAddress) {
        this.mailSender = mailSender;
        this.fromAddress = fromAddress;
    }

    public void sendOtp(String to, String code, String purpose) {
        if (fromAddress == null || fromAddress.isBlank()) {
            throw new RuntimeException("OTP email is not configured on the server.");
        }
        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom(fromAddress);
        message.setTo(to);
        message.setSubject("UFH Campus Security verification code");
        message.setText("Your UFH Campus Security " + purpose + " code is " + code
                + ". It expires in 10 minutes. If you did not request this code, ignore this email.");
        mailSender.send(message);
    }
}
