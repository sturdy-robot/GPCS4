#pragma once

#include "VltCommon.h"
#include "VltHash.h"
#include "Gcn/GcnShaderKey.h"

namespace sce::vlt
{
	/**
     * \brief Shader key
     * 
     * Provides a unique key that can be used
     * to look up a specific shader within a
     * structure. This consists of the shader
     * stage and the source hash, which should
     * be generated from the original code.
     */
	class VltShaderKey
	{

	public:
		/**
         * \brief Creates default shader key
         */
		VltShaderKey();

		/**
         * \brief Creates shader key
         * 
         * \param [in] stage Shader stage
         * \param [in] hash Shader hash
         */
		VltShaderKey(
			VkShaderStageFlagBits stage,
			gcn::GcnShaderKey     key) :
			m_type(stage),
			m_key(key)
		{
		}

		/**
         * \brief Generates string from shader key
         * \returns String representation of the key
         */
		std::string toString() const;

		/**
         * \brief Computes lookup hash
         * \returns Lookup hash
         */
		size_t hash() const;

		/**
         * \brief Checks whether two keys are equal
         * 
         * \param [in] other The shader key to compare to
         * \returns \c true if the two keys are equal
         */
		bool eq(const VltShaderKey& other) const;

	private:
		VkShaderStageFlags m_type;
		gcn::GcnShaderKey  m_key;
	};

}  // namespace sce::vlt