package com.campus.security.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * Sends the browser to the administrator website when localhost:8080
 * or localhost:8080/admin is opened.
 */
@Controller
public class WebController {

    @GetMapping({"/", "/admin", "/admin/"})
    public String adminWebsite() {
        return "forward:/admin/index.html";
    }
}
