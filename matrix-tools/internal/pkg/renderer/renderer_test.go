// Copyright 2025 New Vector Ltd
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial

package renderer

import (
	"os"
	"reflect"
	"testing"
)

func TestRenderConfig(t *testing.T) {
	hostname, _ := os.Hostname()
	droppedFromHostname := hostname[2:4]

	testCases := []struct {
		name     string
		files    []string
		env      map[string]string
		expected map[string]any
		err      bool
	}{
		{
			name:  "Single File",
			files: []string{"testdata/single_file.yml"},
			env: map[string]string{
				"TEST_ENV":      "value",
				"SECRET_KEY":    "secret://testdata/secret_key",
				"THIS_HOSTNAME": "hostname://" + droppedFromHostname,
			},
			expected: map[string]any{
				"key":       "value",
				"secretKey": "secret_value",
				"hostname":  hostname[0:2] + hostname[4:],
			},
			err: false,
		},
		{
			name:  "Multiple Files",
			files: []string{"testdata/multiple_files_1.yml", "testdata/multiple_files_2.yml"},
			env: map[string]string{
				"TEST_ENV_1": "env_value_1",
				"TEST_ENV_2": "env_value_2",
			},
			expected: map[string]any{
				"key_1": "value1",
				"key2":  "value2",
				"keyWithEnv1": map[string]any{
					"env1": "env_value_1",
				},
				"keyWithEnv2": map[string]any{
					"content_with_env2": "env_value_2",
				},
			},
			err: false,
		},
		{
			name:  "Overrides in order",
			files: []string{"testdata/000_override.yml", "testdata/001_override.yml"},
			expected: map[string]any{
				"overriddenKey": "value_001",
				"overriddenArray": []any{
					"item_001_a",
					"item_001_b",
				},
				"overriddenObject": map[string]any{
					"childKey": "value_001",
				},
			},
			err: false,
		},
		{
			name:     "File Does Not Exist",
			files:    []string{"testdata/nonexistent_file.yml"},
			expected: nil,
			err:      true,
		},
		{
			name:     "Environment Variable Missing",
			files:    []string{"testdata/env_var_missing.yml"},
			expected: nil,
			err:      true,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			for k, v := range tc.env {
				if err := os.Setenv(k, v); err != nil {
					t.Errorf("Failed to set environment variable %s: %v", k, err)
				}
			}

			result, err := RenderConfig(tc.files)
			if (err != nil) != tc.err {
				t.Errorf("expected error: %v, got: %v", tc.err, err)
			}
			if !tc.err && !reflect.DeepEqual(result, tc.expected) {
				t.Errorf("expected: %v, got: %v", tc.expected, result)
			}
			for k := range tc.env {
				os.Unsetenv(k)
			}
		})
	}
}
