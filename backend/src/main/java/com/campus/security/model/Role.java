package com.campus.security.model;

import jakarta.persistence.*;

@Entity
@Table(name = "roles")
public class Role {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "role_id")
    private Integer roleId;

    @Column(name = "role_name", nullable = false, unique = true)
    private String roleName;

    @Column(name = "description")
    private String description;

    // Empty constructor required by JPA
    public Role() {
    }

    // Constructor
    public Role(String roleName, String description) {
        this.roleName = roleName;
        this.description = description;
    }

    // Getter for roleId
    public Integer getRoleId() {
        return roleId;
    }

    // Setter for roleId
    public void setRoleId(Integer roleId) {
        this.roleId = roleId;
    }

    // Getter for roleName
    public String getRoleName() {
        return roleName;
    }

    // Setter for roleName
    public void setRoleName(String roleName) {
        this.roleName = roleName;
    }

    // Getter for description
    public String getDescription() {
        return description;
    }

    // Setter for description
    public void setDescription(String description) {
        this.description = description;
    }
}